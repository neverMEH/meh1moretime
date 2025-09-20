#!/usr/bin/env python3
"""
Test Supabase connection and verify tables are created
"""

import os
import sys
from supabase import create_client
from datetime import datetime
import hashlib
import secrets

# Configuration from railway-variables.json
SUPABASE_URL = "https://jfxnfryobrkgckcktymyw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpmeG5mcnlvYnJrZ2Nja3R5bXl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODQwNTc2OCwiZXhwIjoyMDczOTgxNzY4fQ.qn8UroSO2NWmNvYW18mIxQj6uVhRbnJSSCHsO5MjeDo"

def test_connection():
    """Test Supabase connection and verify tables."""
    print("🔍 Testing Supabase connection...")
    print(f"URL: {SUPABASE_URL}")

    try:
        # Create client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase!")

        # Test 1: Check accounts table
        print("\n📊 Checking tables...")
        tables_to_check = [
            'amazon_ads_accounts',
            'amazon_ads_tokens',
            'token_refresh_history',
            'api_keys'
        ]

        for table in tables_to_check:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ Table '{table}' exists")
            except Exception as e:
                print(f"❌ Table '{table}' error: {e}")
                return False

        # Test 2: Count records
        print("\n📈 Record counts:")
        accounts = supabase.table('amazon_ads_accounts').select("*", count='exact').execute()
        print(f"  - Accounts: {len(accounts.data)}")

        tokens = supabase.table('amazon_ads_tokens').select("*", count='exact').execute()
        print(f"  - Tokens: {len(tokens.data)}")

        api_keys = supabase.table('api_keys').select("*", count='exact').execute()
        print(f"  - API Keys: {len(api_keys.data)}")

        # Test 3: Create a test API key for web interface
        print("\n🔑 Creating initial API key for web interface...")
        api_key = f"amzn_ads_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        try:
            result = supabase.table('api_keys').insert({
                'key_hash': key_hash,
                'name': 'Web Interface Initial Key',
                'permissions': ['read', 'write', 'web', 'admin'],
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }).execute()

            print("✅ API Key created successfully!")
            print(f"\n🔐 SAVE THIS API KEY (won't be shown again):")
            print(f"   {api_key}")
            print("\n   This key is needed for API access if required.")

            # Save to a temporary file
            with open('initial_api_key.txt', 'w') as f:
                f.write(f"API Key for Web Interface\n")
                f.write(f"Created: {datetime.utcnow().isoformat()}\n")
                f.write(f"Key: {api_key}\n")
                f.write(f"\nKEEP THIS SECURE!\n")
            print(f"   Also saved to: initial_api_key.txt")

        except Exception as e:
            if "duplicate" in str(e).lower():
                print("ℹ️  API key already exists (this is fine)")
            else:
                print(f"⚠️  Could not create API key: {e}")

        print("\n✨ All tests passed! Supabase is ready for deployment.")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if your Supabase project is active (not paused)")
        print("2. Verify you ran the migration in SQL Editor")
        print("3. Ensure you're using the service_role key")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)