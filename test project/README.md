# Amazon Ads API Token Manager

A secure, thread-safe Python library for managing OAuth2 authentication tokens for the Amazon Advertising API. This implementation handles the complete OAuth2 flow including authorization code exchange, automatic token refresh, and secure local storage.

## Features

✅ **Complete OAuth2 Flow** - Authorization code exchange and token refresh
✅ **Automatic Token Refresh** - Proactive refresh before expiration
✅ **Secure Storage** - Encrypted local token storage
✅ **Thread-Safe** - Concurrent access with proper locking
✅ **Zero Dependencies** - Uses only Python standard library
✅ **Error Recovery** - Robust error handling and retry logic

## Installation

Simply copy `amazon_ads_token_manager.py` to your project:

```bash
# No pip install needed - uses standard library only
cp amazon_ads_token_manager.py your_project/
```

## Quick Start

```python
from amazon_ads_token_manager import AmazonAdsTokenManager

# Initialize the manager
manager = AmazonAdsTokenManager(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# First-time authentication
auth_code = "code_from_oauth_redirect"
tokens = manager.authenticate_with_code(auth_code)

# Get access token (auto-refreshes if needed)
access_token = manager.get_access_token()

# Get headers for API calls
headers = manager.get_headers()
# Makes API call with headers
```

## Complete Usage Guide

### 1. Initial Authentication

```python
# Step 1: Initialize manager
manager = AmazonAdsTokenManager(
    client_id="amzn1.application-oa2-client.xxxxx",
    client_secret="your-secret-here",
    redirect_uri="https://localhost"  # Must match app config
)

# Step 2: Direct user to authorization URL
auth_url = f"https://www.amazon.com/ap/oa?client_id={client_id}&scope=cpc_advertising:campaign_management&response_type=code&redirect_uri=https://localhost"

# Step 3: Exchange authorization code for tokens
auth_code = "AuthorizationCodeFromRedirect"
tokens = manager.authenticate_with_code(auth_code)
```

### 2. Using Existing Refresh Token

```python
# Option A: Tokens auto-load from storage
manager = AmazonAdsTokenManager(client_id, client_secret)

# Option B: Manually set refresh token
manager = AmazonAdsTokenManager(client_id, client_secret)
manager.set_refresh_token("Atzr|existing_refresh_token")
```

### 3. Making API Calls

```python
# Get headers with valid token (auto-refreshes)
headers = manager.get_headers()

# Use with urllib (standard library)
from urllib.request import Request, urlopen
request = Request(
    "https://advertising-api.amazon.com/v2/profiles",
    headers=headers
)
with urlopen(request) as response:
    data = json.loads(response.read())

# Or use with requests library
import requests
response = requests.get(
    "https://advertising-api.amazon.com/v2/profiles",
    headers=headers
)
```

### 4. Token Information

```python
# Check token status
info = manager.get_token_info()
print(f"Status: {info['status']}")
print(f"Expires in: {info['expires_in_seconds']} seconds")
print(f"Is expired: {info['is_expired']}")
```

## Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `client_id` | Amazon LWA client ID | Required |
| `client_secret` | Amazon LWA client secret | Required |
| `storage_path` | Path for encrypted token storage | `.amazon_ads_tokens.json` |
| `redirect_uri` | OAuth redirect URI | `https://localhost` |
| `refresh_buffer` | Seconds before expiry to refresh | 300 (5 minutes) |

## Security Features

- **Encrypted Storage**: Tokens are encrypted using your client secret before storage
- **File Permissions**: Storage file is created with 0600 permissions (owner read/write only)
- **Thread Safety**: All token operations are protected with threading locks
- **No Plain Text**: Tokens are never stored in plain text

## API Reference

### Core Methods

#### `authenticate_with_code(authorization_code: str)`
Exchange authorization code for access and refresh tokens.

#### `get_access_token() -> str`
Get valid access token, automatically refreshing if expired.

#### `get_headers() -> Dict[str, str]`
Get authorization headers for API requests.

#### `refresh_access_token()`
Manually refresh the access token.

#### `set_refresh_token(refresh_token: str)`
Set an existing refresh token for re-authentication.

#### `get_token_info() -> Dict`
Get information about current token status.

#### `clear_tokens()`
Clear all stored tokens and delete storage file.

## Error Handling

The library includes comprehensive error handling:

```python
try:
    access_token = manager.get_access_token()
except Exception as e:
    if "Not authenticated" in str(e):
        # Need initial authentication
        pass
    elif "Token refresh failed" in str(e):
        # Refresh token might be invalid
        pass
    else:
        # Other error
        pass
```

## Thread Safety

The manager is fully thread-safe for concurrent usage:

```python
import threading

def worker():
    token = manager.get_access_token()
    # Make API call

# Safe for multiple threads
threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

## Token Lifecycle

1. **Initial Auth**: Exchange authorization code for tokens
2. **Storage**: Tokens encrypted and saved locally
3. **Usage**: Access token retrieved for API calls
4. **Auto-Refresh**: Tokens refreshed 5 minutes before expiry
5. **Cleanup**: Tokens cleared when no longer needed

## Examples

See `example_usage.py` for complete working examples including:
- Initial authentication flow
- Re-authentication with existing tokens
- Batch API operations
- Error handling

## Testing

```python
# Run the example script
python example_usage.py

# Or run the main module
python amazon_ads_token_manager.py
```

## Requirements

- Python 3.8 or higher
- No external dependencies (uses standard library only)

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please refer to the [project documentation](.agent-os/product/mission.md) or create an issue in the repository.

## Project Structure

```
.
├── amazon_ads_token_manager.py  # Main library file
├── example_usage.py             # Usage examples
├── README.md                    # This file
└── .agent-os/
    └── product/
        ├── mission.md           # Product mission
        ├── mission-lite.md      # Condensed mission
        ├── tech-stack.md        # Technical stack
        └── roadmap.md           # Development roadmap
```