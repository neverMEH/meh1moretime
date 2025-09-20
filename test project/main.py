#!/usr/bin/env python3
"""
FastAPI Web Service for Amazon Ads Token Manager

RESTful API for managing Amazon Advertising OAuth2 tokens.
Deployed on Railway with Supabase backend.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
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
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize managers
token_manager: Optional[SupabaseTokenManager] = None
api_key_manager: Optional[ApiKeyManager] = None

# Security
security = HTTPBearer()


# Pydantic models for request/response
class AccountCreateRequest(BaseModel):
    account_name: str = Field(..., description="Friendly name for the account")
    client_id: str = Field(..., description="Amazon LWA client ID")
    client_secret: str = Field(..., description="Amazon LWA client secret")
    redirect_uri: str = Field(default="https://localhost", description="OAuth redirect URI")


class AuthCodeRequest(BaseModel):
    authorization_code: str = Field(..., description="OAuth authorization code")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Existing refresh token for re-authentication")


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., description="Descriptive name for the API key")
    account_id: Optional[str] = Field(None, description="Optional account restriction")
    permissions: List[str] = Field(default=["read", "write"], description="Key permissions")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    expires_at: str
    needs_refresh: bool


class AccountResponse(BaseModel):
    id: str
    account_name: str
    client_id: str
    redirect_uri: str
    created_at: str
    is_active: bool


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    environment: str
    database: str


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

    print(f"🚀 Amazon Ads Token Manager started in {ENVIRONMENT} mode")

    yield

    # Shutdown
    if token_manager:
        await token_manager.close()
    print("👋 Amazon Ads Token Manager shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Amazon Ads Token Manager API",
    description="Secure OAuth2 token management for Amazon Advertising API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for API key authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Authorization header."""
    api_key = credentials.credentials

    if not api_key_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    key_data = await api_key_manager.verify_api_key(api_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )

    return key_data


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        environment=ENVIRONMENT,
        database="connected" if token_manager else "disconnected"
    )


# Account management endpoints
@app.post("/api/accounts", response_model=AccountResponse)
async def create_account(
    request: AccountCreateRequest,
    api_key: dict = Depends(verify_api_key)
):
    """Create a new Amazon Ads account configuration."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        config = AccountConfig(
            account_name=request.account_name,
            client_id=request.client_id,
            client_secret=request.client_secret,
            redirect_uri=request.redirect_uri
        )

        account = await token_manager.create_account(config)

        return AccountResponse(
            id=account['id'],
            account_name=account['account_name'],
            client_id=account['client_id'],
            redirect_uri=account['redirect_uri'],
            created_at=account['created_at'],
            is_active=account['is_active']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/accounts", response_model=List[AccountResponse])
async def list_accounts(api_key: dict = Depends(verify_api_key)):
    """List all configured accounts."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    accounts = await token_manager.list_accounts()

    return [
        AccountResponse(
            id=acc['id'],
            account_name=acc['account_name'],
            client_id=acc['client_id'],
            redirect_uri=acc['redirect_uri'],
            created_at=acc['created_at'],
            is_active=acc['is_active']
        )
        for acc in accounts
    ]


@app.get("/api/accounts/{account_id}")
async def get_account(
    account_id: str,
    api_key: dict = Depends(verify_api_key)
):
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
            detail=f"Account {account_id} not found"
        )

    # Remove sensitive data
    account.pop('client_secret', None)
    account.pop('client_secret_encrypted', None)

    return account


# Token management endpoints
@app.post("/api/accounts/{account_id}/authenticate")
async def authenticate_account(
    account_id: str,
    request: AuthCodeRequest,
    api_key: dict = Depends(verify_api_key)
):
    """Exchange authorization code for tokens."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        result = await token_manager.authenticate_with_code(
            account_id,
            request.authorization_code
        )

        return {
            "success": True,
            "token_id": result['token_id'],
            "expires_at": result['expires_at'],
            "expires_in": result['expires_in']
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@app.post("/api/accounts/{account_id}/refresh")
async def refresh_token(
    account_id: str,
    api_key: dict = Depends(verify_api_key)
):
    """Manually refresh the access token."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        result = await token_manager.refresh_access_token(account_id)

        return {
            "success": True,
            "expires_at": result['expires_at'],
            "expires_in": result['expires_in'],
            "refresh_count": result['refresh_count']
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}"
        )


@app.get("/api/accounts/{account_id}/token", response_model=TokenResponse)
async def get_token(
    account_id: str,
    api_key: dict = Depends(verify_api_key)
):
    """Get valid access token (auto-refreshes if needed)."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        access_token = await token_manager.get_access_token(account_id)
        info = await token_manager.get_token_info(account_id)

        return TokenResponse(
            access_token=access_token,
            expires_in=info['expires_in_seconds'],
            expires_at=info['expires_at'],
            needs_refresh=info['needs_refresh']
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get token: {str(e)}"
        )


@app.get("/api/accounts/{account_id}/status")
async def get_token_status(
    account_id: str,
    api_key: dict = Depends(verify_api_key)
):
    """Get token status information."""
    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    info = await token_manager.get_token_info(account_id)

    if info['status'] == 'error':
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=info.get('error', 'Unknown error')
        )

    return info


# API Key management endpoints
@app.post("/api/keys")
async def create_api_key(
    request: ApiKeyCreateRequest,
    api_key: dict = Depends(verify_api_key)
):
    """Create a new API key (requires admin permissions)."""
    # Check if current key has admin permissions
    if 'admin' not in api_key.get('permissions', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )

    if not api_key_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    try:
        new_key = await api_key_manager.create_api_key(
            name=request.name,
            account_id=request.account_id,
            permissions=request.permissions,
            expires_in_days=request.expires_in_days
        )

        return {
            "api_key": new_key['api_key'],
            "key_id": new_key['key_id'],
            "name": new_key['name'],
            "expires_at": new_key['expires_at'],
            "warning": "Save this API key securely. It cannot be retrieved again."
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Utility endpoints
@app.post("/api/cleanup")
async def cleanup_expired_tokens(api_key: dict = Depends(verify_api_key)):
    """Clean up expired tokens (admin only)."""
    if 'admin' not in api_key.get('permissions', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )

    if not token_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )

    await token_manager.cleanup_expired_tokens()

    return {"success": True, "message": "Expired tokens cleaned up"}


@app.get("/api/oauth/url/{account_id}")
async def get_oauth_url(
    account_id: str,
    api_key: dict = Depends(verify_api_key)
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
            detail=f"Account {account_id} not found"
        )

    auth_url = (
        f"https://www.amazon.com/ap/oa"
        f"?client_id={account['client_id']}"
        f"&scope=cpc_advertising:campaign_management"
        f"&response_type=code"
        f"&redirect_uri={account['redirect_uri']}"
    )

    return {
        "auth_url": auth_url,
        "instructions": "Direct user to auth_url, then POST the code to /api/accounts/{account_id}/authenticate"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Amazon Ads Token Manager API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "documentation": "/docs",
        "health": "/health"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
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
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development"
    )