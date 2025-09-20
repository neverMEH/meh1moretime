#!/usr/bin/env python3
"""
Example usage of Amazon Ads Token Manager

This script demonstrates how to use the token manager for:
1. Initial authentication with authorization code
2. Automatic token refresh
3. Making API calls with managed tokens
"""

from amazon_ads_token_manager import AmazonAdsTokenManager
import json
import sys


def initial_authentication_example():
    """Example of first-time authentication flow."""

    # Your Amazon Advertising API credentials
    CLIENT_ID = "amzn1.application-oa2-client.xxxxx"
    CLIENT_SECRET = "your-client-secret-here"

    # Initialize the token manager
    token_manager = AmazonAdsTokenManager(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        storage_path=".amazon_ads_tokens.json",
        redirect_uri="https://localhost"  # Must match your app settings
    )

    # Step 1: Direct user to authorization URL
    auth_url = (
        f"https://www.amazon.com/ap/oa"
        f"?client_id={CLIENT_ID}"
        f"&scope=cpc_advertising:campaign_management"
        f"&response_type=code"
        f"&redirect_uri=https://localhost"
    )

    print("Step 1: Direct user to this URL for authorization:")
    print(auth_url)
    print("\nStep 2: After authorization, user will be redirected to:")
    print("https://localhost?code=AUTHORIZATION_CODE")

    # Step 3: Exchange authorization code for tokens
    auth_code = input("\nStep 3: Enter the authorization code from redirect URL: ")

    try:
        tokens = token_manager.authenticate_with_code(auth_code)
        print("\nSuccess! Tokens obtained and stored securely.")
        print(f"Access token expires in: {tokens['expires_in']} seconds")
    except Exception as e:
        print(f"\nError during authentication: {e}")
        sys.exit(1)

    return token_manager


def re_authentication_example():
    """Example of re-authentication with existing refresh token."""

    CLIENT_ID = "amzn1.application-oa2-client.xxxxx"
    CLIENT_SECRET = "your-client-secret-here"

    # Initialize manager
    token_manager = AmazonAdsTokenManager(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # Option 1: Load from existing storage file
    # (tokens are automatically loaded from storage_path)

    # Option 2: Manually set refresh token
    # refresh_token = "Atzr|xxxxx"  # Your existing refresh token
    # token_manager.set_refresh_token(refresh_token)

    return token_manager


def api_call_example(token_manager: AmazonAdsTokenManager):
    """Example of making API calls with automatic token management."""

    # The manager handles token refresh automatically
    # Just get the headers whenever you need them

    print("\n" + "="*50)
    print("Making API calls with managed tokens")
    print("="*50)

    # Check token status
    info = token_manager.get_token_info()
    print(f"\nToken status: {json.dumps(info, indent=2)}")

    # Example API calls (using standard library)
    from urllib.request import Request, urlopen

    try:
        # Get headers with valid access token
        # This automatically refreshes if expired
        headers = token_manager.get_headers()

        # Example: Get advertising profiles
        api_url = "https://advertising-api.amazon.com/v2/profiles"

        request = Request(api_url, headers=headers)

        # Make the API call
        # with urlopen(request) as response:
        #     data = json.loads(response.read().decode())
        #     print(f"\nAPI Response: {json.dumps(data, indent=2)}")

        print(f"\nReady to make API calls with headers:")
        print(f"Authorization: {headers['Authorization'][:30]}...")

    except Exception as e:
        print(f"\nError making API call: {e}")


def batch_operations_example(token_manager: AmazonAdsTokenManager):
    """Example of handling multiple API calls with token management."""

    print("\n" + "="*50)
    print("Batch operations with automatic token refresh")
    print("="*50)

    # Simulate multiple API calls over time
    import time

    for i in range(3):
        print(f"\n--- API Call {i+1} ---")

        # Get current token info
        info = token_manager.get_token_info()
        print(f"Token expires in: {info['expires_in_seconds']} seconds")

        # Get headers (auto-refreshes if needed)
        headers = token_manager.get_headers()
        print(f"Headers ready for API call {i+1}")

        # Simulate API call delay
        time.sleep(2)

    print("\nAll batch operations completed successfully!")


def main():
    """Main example runner."""

    print("Amazon Ads API Token Manager - Examples")
    print("="*50)

    print("\nSelect an example to run:")
    print("1. Initial authentication (first time)")
    print("2. Re-authentication (with existing tokens)")
    print("3. Simulate API calls")

    choice = input("\nEnter choice (1-3): ")

    if choice == "1":
        # Initial authentication flow
        token_manager = initial_authentication_example()
        api_call_example(token_manager)

    elif choice == "2":
        # Re-authentication with existing tokens
        token_manager = re_authentication_example()

        # Check if we have tokens
        info = token_manager.get_token_info()
        if info['status'] == 'not_authenticated':
            print("\nNo existing tokens found. Please run initial authentication first.")
            sys.exit(1)

        api_call_example(token_manager)
        batch_operations_example(token_manager)

    elif choice == "3":
        # Load existing tokens and simulate API calls
        CLIENT_ID = input("Enter client ID: ")
        CLIENT_SECRET = input("Enter client secret: ")

        token_manager = AmazonAdsTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )

        info = token_manager.get_token_info()
        if info['status'] == 'not_authenticated':
            print("\nNo tokens found. Running initial authentication...")
            auth_code = input("Enter authorization code: ")
            token_manager.authenticate_with_code(auth_code)

        api_call_example(token_manager)
        batch_operations_example(token_manager)

    else:
        print("Invalid choice")
        sys.exit(1)

    print("\n" + "="*50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()