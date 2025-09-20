#!/usr/bin/env python3
"""
Amazon Ads API Token Manager

A secure OAuth2 token management library for Amazon Advertising API.
Handles authorization code exchange, automatic token refresh, and secure storage.
"""

import json
import time
import os
import hashlib
import base64
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class AmazonAdsTokenManager:
    """Manages OAuth2 tokens for Amazon Advertising API with automatic refresh."""

    TOKEN_ENDPOINT = "https://api.amazon.com/auth/o2/token"
    REFRESH_BUFFER_SECONDS = 300  # Refresh 5 minutes before expiration

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        storage_path: str = ".amazon_ads_tokens.json",
        redirect_uri: str = "https://localhost",
        refresh_buffer: int = None
    ):
        """
        Initialize the token manager.

        Args:
            client_id: LWA application client ID
            client_secret: LWA application client secret
            storage_path: Path to store encrypted tokens
            redirect_uri: OAuth redirect URI (must match app configuration)
            refresh_buffer: Seconds before expiration to refresh (default 300)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.storage_path = Path(storage_path)
        self.redirect_uri = redirect_uri
        self.refresh_buffer = refresh_buffer or self.REFRESH_BUFFER_SECONDS

        # Thread safety
        self._lock = threading.Lock()
        self._tokens: Optional[Dict[str, Any]] = None
        self._load_tokens()

    def _encrypt_data(self, data: str) -> str:
        """Simple encryption using client secret as key."""
        key = hashlib.sha256(self.client_secret.encode()).digest()
        encrypted = bytearray()
        for i, char in enumerate(data.encode()):
            encrypted.append(char ^ key[i % len(key)])
        return base64.b64encode(encrypted).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data encrypted with _encrypt_data."""
        key = hashlib.sha256(self.client_secret.encode()).digest()
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ key[i % len(key)])
        return decrypted.decode()

    def _save_tokens(self) -> None:
        """Save tokens to encrypted storage file."""
        if self._tokens:
            data = json.dumps(self._tokens)
            encrypted = self._encrypt_data(data)

            # Create directory if needed
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with restricted permissions
            with open(self.storage_path, 'w') as f:
                json.dump({"encrypted": encrypted}, f)

            # Set file permissions (Unix-like systems)
            try:
                os.chmod(self.storage_path, 0o600)
            except:
                pass  # Windows doesn't support chmod

    def _load_tokens(self) -> None:
        """Load tokens from encrypted storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                if "encrypted" in data:
                    decrypted = self._decrypt_data(data["encrypted"])
                    self._tokens = json.loads(decrypted)
                else:
                    # Legacy unencrypted format
                    self._tokens = data
            except Exception as e:
                print(f"Warning: Could not load tokens: {e}")
                self._tokens = None

    def _make_request(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Make HTTP POST request to token endpoint."""
        encoded_data = urlencode(data).encode('utf-8')

        request = Request(
            self.TOKEN_ENDPOINT,
            data=encoded_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': str(len(encoded_data))
            },
            method='POST'
        )

        try:
            with urlopen(request) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"OAuth error: {e.code} - {error_body}")
        except URLError as e:
            raise Exception(f"Network error: {e.reason}")

    def authenticate_with_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens (initial authentication).

        Args:
            authorization_code: The authorization code from OAuth flow

        Returns:
            Token response dictionary
        """
        with self._lock:
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri
            }

            response = self._make_request(data)

            # Store tokens with expiration timestamp
            self._tokens = {
                'access_token': response['access_token'],
                'refresh_token': response['refresh_token'],
                'expires_in': response['expires_in'],
                'token_type': response.get('token_type', 'Bearer'),
                'expiration_timestamp': time.time() + response['expires_in'],
                'created_at': datetime.utcnow().isoformat()
            }

            self._save_tokens()
            return self._tokens

    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using the refresh token.

        Returns:
            Updated token response dictionary
        """
        with self._lock:
            if not self._tokens or 'refresh_token' not in self._tokens:
                raise Exception("No refresh token available. Please authenticate first.")

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self._tokens['refresh_token'],
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            try:
                response = self._make_request(data)

                # Update tokens with new access token
                self._tokens.update({
                    'access_token': response['access_token'],
                    'expires_in': response['expires_in'],
                    'expiration_timestamp': time.time() + response['expires_in'],
                    'last_refreshed': datetime.utcnow().isoformat()
                })

                # Some providers return new refresh token
                if 'refresh_token' in response:
                    self._tokens['refresh_token'] = response['refresh_token']

                self._save_tokens()
                return self._tokens

            except Exception as e:
                print(f"Token refresh failed: {e}")
                raise

    def is_token_expired(self) -> bool:
        """Check if the current access token is expired or near expiration."""
        if not self._tokens or 'expiration_timestamp' not in self._tokens:
            return True

        # Check if token expires within buffer time
        return time.time() >= (self._tokens['expiration_timestamp'] - self.refresh_buffer)

    def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token for API requests
        """
        with self._lock:
            if not self._tokens:
                raise Exception("Not authenticated. Please call authenticate_with_code first.")

            # Check and refresh if needed
            if self.is_token_expired():
                print("Token expired or expiring soon, refreshing...")
                self.refresh_access_token()

            return self._tokens['access_token']

    def get_headers(self) -> Dict[str, str]:
        """
        Get authorization headers for API requests.

        Returns:
            Dictionary with Authorization header
        """
        token = self.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def set_refresh_token(self, refresh_token: str) -> None:
        """
        Set refresh token for re-authentication scenarios.

        Args:
            refresh_token: Existing refresh token to use
        """
        with self._lock:
            if not self._tokens:
                self._tokens = {}

            self._tokens['refresh_token'] = refresh_token
            self._tokens['manual_refresh_set'] = datetime.utcnow().isoformat()
            self._save_tokens()

    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about current tokens (for debugging).

        Returns:
            Token information with sensitive data redacted
        """
        if not self._tokens:
            return {"status": "not_authenticated"}

        info = {
            "status": "authenticated",
            "has_access_token": bool(self._tokens.get('access_token')),
            "has_refresh_token": bool(self._tokens.get('refresh_token')),
            "expires_in_seconds": None,
            "created_at": self._tokens.get('created_at'),
            "last_refreshed": self._tokens.get('last_refreshed')
        }

        if 'expiration_timestamp' in self._tokens:
            remaining = self._tokens['expiration_timestamp'] - time.time()
            info['expires_in_seconds'] = max(0, int(remaining))
            info['is_expired'] = self.is_token_expired()

        return info

    def clear_tokens(self) -> None:
        """Clear all stored tokens and delete storage file."""
        with self._lock:
            self._tokens = None
            if self.storage_path.exists():
                self.storage_path.unlink()


# Example usage and helper functions
def main():
    """Example usage of the Amazon Ads Token Manager."""

    # Example configuration
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"

    # Initialize manager
    manager = AmazonAdsTokenManager(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        storage_path=".amazon_ads_tokens.json",
        redirect_uri="https://localhost"
    )

    print("Amazon Ads Token Manager initialized")
    print("=" * 50)

    # Check current status
    info = manager.get_token_info()
    print(f"Current status: {info['status']}")

    if info['status'] == 'not_authenticated':
        print("\nTo authenticate, you need to:")
        print("1. Direct user to Amazon OAuth URL")
        print("2. Get authorization code from redirect")
        print("3. Call manager.authenticate_with_code(code)")

        # Example: First-time authentication
        # auth_code = input("Enter authorization code: ")
        # tokens = manager.authenticate_with_code(auth_code)
        # print(f"Authenticated! Access token obtained.")
    else:
        print(f"Has access token: {info['has_access_token']}")
        print(f"Has refresh token: {info['has_refresh_token']}")
        print(f"Expires in: {info['expires_in_seconds']} seconds")
        print(f"Is expired: {info['is_expired']}")

        try:
            # Get valid access token (auto-refreshes if needed)
            access_token = manager.get_access_token()
            print(f"\nAccess token retrieved (first 20 chars): {access_token[:20]}...")

            # Get headers for API request
            headers = manager.get_headers()
            print(f"Authorization header ready for API calls")

        except Exception as e:
            print(f"Error getting access token: {e}")

    print("\n" + "=" * 50)
    print("Example API usage:")
    print("headers = manager.get_headers()")
    print("response = requests.get(api_url, headers=headers)")


if __name__ == "__main__":
    main()