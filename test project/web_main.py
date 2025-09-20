#!/usr/bin/env python3
"""
FastAPI Web Application for Amazon Ads Token Manager

Web interface with OAuth flow for managing Amazon Advertising tokens.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, Field
import uvicorn

from supabase_token_manager import (
    SupabaseTokenManager,
    AccountConfig,
    ApiKeyManager
)

# Environment configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

# Initialize managers
token_manager: Optional[SupabaseTokenManager] = None
api_key_manager: Optional[ApiKeyManager] = None

# Session management
sessions: Dict[str, Dict] = {}
cookie_sec = APIKeyCookie(name="session_id", auto_error=False)

# Templates
templates = Jinja2Templates(directory="templates")


# Pydantic models
class WebAccountCreate(BaseModel):
    account_name: str
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None


class OAuthCallback(BaseModel):
    account_id: str
    code: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global token_manager, api_key_manager

    # Startup
    token_manager = SupabaseTokenManager(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        encryption_key=ENCRYPTION_KEY
    )

    from supabase import create_client
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    api_key_manager = ApiKeyManager(supabase_client)

    # Create default web API key if it doesn't exist
    try:
        web_key = await api_key_manager.create_api_key(
            name="Web Interface",
            permissions=["read", "write", "web"],
            expires_in_days=365
        )
        print(f"📝 Web API Key: {web_key['api_key']}")
    except:
        pass  # Key might already exist

    print(f"🚀 Web interface started at {APP_URL}")
    print(f"🌐 Environment: {ENVIRONMENT}")

    yield

    # Shutdown
    if token_manager:
        await token_manager.close()
    print("👋 Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Amazon Ads Token Manager",
    description="Web interface for managing Amazon Advertising OAuth tokens",
    version="3.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Session management
def get_session(session_id: Optional[str] = Depends(cookie_sec)) -> Dict:
    """Get or create session."""
    if not session_id or session_id not in sessions:
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "data": {}
        }
    return sessions[session_id]


def create_session_response(response: Response, session: Dict):
    """Set session cookie in response."""
    response.set_cookie(
        key="session_id",
        value=session["id"],
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=86400  # 24 hours
    )


# Web routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with connect account form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page showing all accounts."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback_page(request: Request):
    """OAuth callback page."""
    return templates.TemplateResponse("callback.html", {"request": request})


# Web API endpoints
@app.post("/web/accounts")
async def create_web_account(
    account: WebAccountCreate,
    response: Response,
    session: Dict = Depends(get_session)
):
    """Create a new account via web interface."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        # Set redirect URI to our callback
        redirect_uri = account.redirect_uri or f"{APP_URL}/callback"

        config = AccountConfig(
            account_name=account.account_name,
            client_id=account.client_id,
            client_secret=account.client_secret,
            redirect_uri=redirect_uri
        )

        result = await token_manager.create_account(config)

        # Store in session
        session["data"]["last_account_id"] = result["id"]
        create_session_response(response, session)

        return {
            "id": result["id"],
            "account_name": result["account_name"],
            "redirect_uri": redirect_uri
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/web/accounts")
async def list_web_accounts(session: Dict = Depends(get_session)):
    """List all accounts with token status."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    accounts = await token_manager.list_accounts()

    # Add token info for each account
    for account in accounts:
        try:
            token_info = await token_manager.get_token_info(account["id"])
            account["token_info"] = token_info
        except:
            account["token_info"] = {"status": "not_authenticated"}

    return accounts


@app.get("/web/oauth/{account_id}")
async def get_oauth_url(
    account_id: str,
    response: Response,
    session: Dict = Depends(get_session)
):
    """Get OAuth authorization URL for an account."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    account = await token_manager.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Store account ID in session for callback
    session["data"]["pending_account_id"] = account_id
    create_session_response(response, session)

    # Build OAuth URL
    auth_url = (
        f"https://www.amazon.com/ap/oa"
        f"?client_id={account['client_id']}"
        f"&scope=cpc_advertising:campaign_management"
        f"&response_type=code"
        f"&redirect_uri={account['redirect_uri']}"
    )

    return {
        "auth_url": auth_url,
        "account_id": account_id
    }


@app.post("/web/callback")
async def process_oauth_callback(
    callback: OAuthCallback,
    response: Response,
    session: Dict = Depends(get_session)
):
    """Process OAuth callback with authorization code."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        # Exchange code for tokens
        result = await token_manager.authenticate_with_code(
            callback.account_id,
            callback.code
        )

        # Clear pending from session
        if "pending_account_id" in session["data"]:
            del session["data"]["pending_account_id"]
        create_session_response(response, session)

        return {
            "success": True,
            "token_id": result["token_id"],
            "expires_in": result["expires_in"],
            "expires_at": result["expires_at"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/web/accounts/{account_id}/token")
async def get_web_token(account_id: str, session: Dict = Depends(get_session)):
    """Get access token for an account."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        access_token = await token_manager.get_access_token(account_id)
        token_info = await token_manager.get_token_info(account_id)

        return {
            "access_token": access_token,
            "expires_in": token_info["expires_in_seconds"],
            "expires_at": token_info["expires_at"],
            "needs_refresh": token_info["needs_refresh"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/web/accounts/{account_id}/refresh")
async def refresh_web_token(account_id: str, session: Dict = Depends(get_session)):
    """Manually refresh token for an account."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        result = await token_manager.refresh_access_token(account_id)

        return {
            "success": True,
            "expires_at": result["expires_at"],
            "expires_in": result["expires_in"],
            "refresh_count": result["refresh_count"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/web/accounts/{account_id}")
async def get_web_account(account_id: str, session: Dict = Depends(get_session)):
    """Get account details."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    account = await token_manager.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Remove sensitive data
    account.pop("client_secret", None)
    account.pop("client_secret_encrypted", None)

    # Add token info
    try:
        token_info = await token_manager.get_token_info(account_id)
        account["token_info"] = token_info
    except:
        account["token_info"] = {"status": "not_authenticated"}

    return account


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "sessions_active": len(sessions)
    }


# Session cleanup
@app.on_event("startup")
async def startup_event():
    """Clean up old sessions periodically."""
    import asyncio

    async def cleanup_sessions():
        while True:
            await asyncio.sleep(3600)  # Every hour
            now = datetime.utcnow()
            expired = []
            for sid, session in sessions.items():
                created = datetime.fromisoformat(session["created_at"])
                if (now - created).total_seconds() > 86400:  # 24 hours
                    expired.append(sid)

            for sid in expired:
                del sessions[sid]

            if expired:
                print(f"Cleaned up {len(expired)} expired sessions")

    asyncio.create_task(cleanup_sessions())


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if request.url.path.startswith("/web/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "web_main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development"
    )