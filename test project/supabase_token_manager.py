#!/usr/bin/env python3
"""
Amazon Ads API Token Manager with Supabase Backend

A secure OAuth2 token management system using Supabase for storage.
Handles authorization, automatic refresh, and multi-account management.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
import httpx
from supabase import create_client, Client
from pydantic import BaseModel, Field
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """Token data model for validation."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: Optional[str] = None


class AccountConfig(BaseModel):
    """Amazon Ads account configuration."""
    account_name: str
    client_id: str
    client_secret: str
    redirect_uri: str = "https://localhost"


class SupabaseTokenManager:
    """Manages OAuth2 tokens for Amazon Ads API with Supabase storage."""

    TOKEN_ENDPOINT = "https://api.amazon.com/auth/o2/token"
    REFRESH_BUFFER_SECONDS = 300  # 5 minutes before expiration

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        encryption_key: Optional[str] = None,
        refresh_buffer: int = None
    ):
        """
        Initialize the token manager with Supabase.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/service key
            encryption_key: Key for encrypting tokens (auto-generated if not provided)
            refresh_buffer: Seconds before expiration to refresh
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.refresh_buffer = refresh_buffer or self.REFRESH_BUFFER_SECONDS

        # Setup encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        else:
            # Generate a key from environment or create new
            key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

        # HTTP client for Amazon API calls
        self.http_client = httpx.AsyncClient()

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    async def create_account(self, config: AccountConfig) -> Dict[str, Any]:
        """
        Create a new Amazon Ads account configuration.

        Args:
            config: Account configuration with credentials

        Returns:
            Created account record
        """
        try:
            # Encrypt client secret
            encrypted_secret = self._encrypt(config.client_secret)

            # Insert account
            result = self.supabase.table('amazon_ads_accounts').insert({
                'account_name': config.account_name,
                'client_id': config.client_id,
                'client_secret_encrypted': encrypted_secret,
                'redirect_uri': config.redirect_uri,
                'is_active': True
            }).execute()

            logger.info(f"Created account: {config.account_name}")
            return result.data[0]

        except Exception as e:
            logger.error(f"Failed to create account: {e}")
            raise

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account configuration by ID."""
        try:
            result = self.supabase.table('amazon_ads_accounts').select('*').eq(
                'id', account_id
            ).single().execute()

            if result.data:
                # Decrypt client secret
                result.data['client_secret'] = self._decrypt(
                    result.data['client_secret_encrypted']
                )
                return result.data

            return None

        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return None

    async def authenticate_with_code(
        self,
        account_id: str,
        authorization_code: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Args:
            account_id: Account UUID from Supabase
            authorization_code: OAuth authorization code

        Returns:
            Token response
        """
        try:
            # Get account details
            account = await self.get_account(account_id)
            if not account:
                raise ValueError(f"Account {account_id} not found")

            # Exchange code for tokens
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'client_id': account['client_id'],
                'client_secret': account['client_secret'],
                'redirect_uri': account['redirect_uri']
            }

            response = await self.http_client.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()

            token_data = response.json()

            # Calculate expiration
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data['expires_in']
            )

            # Encrypt tokens
            encrypted_access = self._encrypt(token_data['access_token'])
            encrypted_refresh = self._encrypt(token_data['refresh_token'])

            # Store in Supabase
            token_record = {
                'account_id': account_id,
                'access_token': encrypted_access,
                'refresh_token': encrypted_refresh,
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': expires_at.isoformat(),
                'scope': token_data.get('scope'),
                'is_valid': True
            }

            # Upsert tokens (update if exists, insert if not)
            result = self.supabase.table('amazon_ads_tokens').upsert(
                token_record,
                on_conflict='account_id'
            ).execute()

            # Log the authentication
            await self._log_token_action(
                account_id,
                result.data[0]['id'] if result.data else None,
                'created',
                True
            )

            logger.info(f"Successfully authenticated account {account_id}")
            return {
                'token_id': result.data[0]['id'],
                'expires_at': expires_at.isoformat(),
                'expires_in': token_data['expires_in']
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during authentication: {e}")
            await self._log_token_action(account_id, None, 'created', False, str(e))
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            await self._log_token_action(account_id, None, 'created', False, str(e))
            raise

    async def refresh_access_token(self, account_id: str) -> Dict[str, Any]:
        """
        Refresh the access token for an account.

        Args:
            account_id: Account UUID

        Returns:
            New token information
        """
        try:
            # Get current tokens
            tokens = await self._get_tokens(account_id)
            if not tokens:
                raise ValueError(f"No tokens found for account {account_id}")

            # Get account details
            account = await self.get_account(account_id)
            if not account:
                raise ValueError(f"Account {account_id} not found")

            # Decrypt refresh token
            refresh_token = self._decrypt(tokens['refresh_token'])

            # Request new tokens
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': account['client_id'],
                'client_secret': account['client_secret']
            }

            response = await self.http_client.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()

            token_data = response.json()

            # Calculate new expiration
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data['expires_in']
            )

            # Encrypt new access token
            encrypted_access = self._encrypt(token_data['access_token'])

            # Update tokens in Supabase
            update_data = {
                'access_token': encrypted_access,
                'expires_at': expires_at.isoformat(),
                'last_refreshed_at': datetime.now(timezone.utc).isoformat(),
                'refresh_count': tokens.get('refresh_count', 0) + 1
            }

            # Update refresh token if provided
            if 'refresh_token' in token_data:
                encrypted_refresh = self._encrypt(token_data['refresh_token'])
                update_data['refresh_token'] = encrypted_refresh

            result = self.supabase.table('amazon_ads_tokens').update(
                update_data
            ).eq('account_id', account_id).execute()

            # Log the refresh
            await self._log_token_action(
                account_id,
                tokens['id'],
                'refreshed',
                True
            )

            logger.info(f"Successfully refreshed token for account {account_id}")
            return {
                'expires_at': expires_at.isoformat(),
                'expires_in': token_data['expires_in'],
                'refresh_count': update_data['refresh_count']
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during token refresh: {e}")
            await self._log_token_action(
                account_id,
                tokens.get('id') if tokens else None,
                'refreshed',
                False,
                str(e)
            )
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            await self._log_token_action(
                account_id,
                tokens.get('id') if tokens else None,
                'refreshed',
                False,
                str(e)
            )
            raise

    async def get_access_token(self, account_id: str) -> str:
        """
        Get valid access token, refreshing if necessary.

        Args:
            account_id: Account UUID

        Returns:
            Decrypted access token
        """
        try:
            # Get current tokens
            tokens = await self._get_tokens(account_id)
            if not tokens:
                raise ValueError(f"No tokens found for account {account_id}")

            # Check expiration
            expires_at = datetime.fromisoformat(tokens['expires_at'].replace('Z', '+00:00'))
            buffer_time = timedelta(seconds=self.refresh_buffer)

            if datetime.now(timezone.utc) >= (expires_at - buffer_time):
                logger.info(f"Token expiring soon for account {account_id}, refreshing...")
                await self.refresh_access_token(account_id)
                tokens = await self._get_tokens(account_id)

            # Decrypt and return access token
            return self._decrypt(tokens['access_token'])

        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    async def _get_tokens(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get current tokens for an account."""
        try:
            result = self.supabase.table('amazon_ads_tokens').select('*').eq(
                'account_id', account_id
            ).eq('is_valid', True).single().execute()

            return result.data if result.data else None

        except Exception as e:
            logger.error(f"Failed to get tokens: {e}")
            return None

    async def _log_token_action(
        self,
        account_id: str,
        token_id: Optional[str],
        action: str,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Log token action to history table."""
        try:
            log_entry = {
                'account_id': account_id,
                'token_id': token_id,
                'action': action,
                'success': success,
                'error_message': error_message
            }

            self.supabase.table('token_refresh_history').insert(log_entry).execute()

        except Exception as e:
            logger.warning(f"Failed to log token action: {e}")

    async def get_token_info(self, account_id: str) -> Dict[str, Any]:
        """Get token status information for an account."""
        try:
            tokens = await self._get_tokens(account_id)
            if not tokens:
                return {'status': 'not_authenticated', 'account_id': account_id}

            expires_at = datetime.fromisoformat(tokens['expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            expires_in = (expires_at - now).total_seconds()

            return {
                'status': 'authenticated',
                'account_id': account_id,
                'token_id': tokens['id'],
                'expires_at': expires_at.isoformat(),
                'expires_in_seconds': max(0, int(expires_in)),
                'needs_refresh': expires_in <= self.refresh_buffer,
                'refresh_count': tokens.get('refresh_count', 0),
                'last_refreshed': tokens.get('last_refreshed_at')
            }

        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return {'status': 'error', 'error': str(e)}

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all configured accounts."""
        try:
            result = self.supabase.table('amazon_ads_accounts').select(
                'id, account_name, client_id, redirect_uri, created_at, is_active'
            ).eq('is_active', True).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            return []

    async def cleanup_expired_tokens(self):
        """Mark expired tokens as invalid."""
        try:
            # Call the database function
            self.supabase.rpc('cleanup_expired_tokens', {}).execute()
            logger.info("Cleaned up expired tokens")

        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


# API Key Management
class ApiKeyManager:
    """Manages API keys for service authentication."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def generate_api_key(self) -> str:
        """Generate a new API key."""
        return f"amzn_ads_{secrets.token_urlsafe(32)}"

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def create_api_key(
        self,
        name: str,
        account_id: Optional[str] = None,
        permissions: List[str] = None,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, str]:
        """Create a new API key."""
        api_key = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)

        expires_at = None
        if expires_in_days:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            ).isoformat()

        result = self.supabase.table('api_keys').insert({
            'key_hash': key_hash,
            'name': name,
            'account_id': account_id,
            'permissions': permissions or ['read', 'write'],
            'expires_at': expires_at,
            'is_active': True
        }).execute()

        return {
            'api_key': api_key,
            'key_id': result.data[0]['id'],
            'name': name,
            'expires_at': expires_at
        }

    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify and get API key details."""
        key_hash = self.hash_api_key(api_key)

        try:
            result = self.supabase.table('api_keys').select('*').eq(
                'key_hash', key_hash
            ).eq('is_active', True).single().execute()

            if result.data:
                # Check expiration
                if result.data.get('expires_at'):
                    expires = datetime.fromisoformat(
                        result.data['expires_at'].replace('Z', '+00:00')
                    )
                    if datetime.now(timezone.utc) > expires:
                        return None

                # Update last used
                self.supabase.table('api_keys').update({
                    'last_used_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', result.data['id']).execute()

                return result.data

            return None

        except Exception:
            return None