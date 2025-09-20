# Supabase Setup Guide

This guide will walk you through setting up Supabase for the Amazon Ads Token Manager.

## 📋 Prerequisites

1. A Supabase account (free tier works fine)
2. A new or existing Supabase project

## 🚀 Step-by-Step Setup

### Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign in or create an account
3. Click "New Project"
4. Fill in:
   - **Project name**: amazon-ads-token-manager
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is sufficient

### Step 2: Run the Database Migration

1. In your Supabase dashboard, click on **SQL Editor** (left sidebar)
2. Click **New Query**
3. Copy and paste the entire contents of `supabase_migration_simple.sql`
4. Click **Run** (or press Ctrl+Enter)
5. You should see a success message in the results panel

### Step 3: Get Your API Keys

1. Go to **Settings** → **API** in your Supabase dashboard
2. You'll need two values:

   **Project URL:**
   ```
   https://YOUR_PROJECT_ID.supabase.co
   ```

   **Service Role Key** (for backend - keep secret!):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

   > ⚠️ **Important**: Use the `service_role` key, NOT the `anon` key. The service role key has full access to bypass Row Level Security.

### Step 4: Configure Environment Variables

Create a `.env` file in your project:

```bash
# Supabase Configuration
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Security (generate a new one)
ENCRYPTION_KEY=your-fernet-key-here

# Application
APP_URL=http://localhost:8000
ENVIRONMENT=development
```

To generate an encryption key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Step 5: Verify the Setup

Run this query in the SQL Editor to verify tables were created:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'amazon_ads_accounts',
    'amazon_ads_tokens',
    'token_refresh_history',
    'api_keys'
);
```

You should see all 4 tables listed.

## 🔒 Security Configuration

### Row Level Security (RLS)

The migration enables RLS with permissive policies. This means:
- ✅ Your service role key can access everything
- ⚠️ The anon key has full access (update policies if you need restrictions)

To make it more secure later, you can update the policies:

```sql
-- Example: Restrict to authenticated users only
ALTER POLICY "Allow all operations on accounts" ON amazon_ads_accounts
    TO authenticated;
```

### Encryption

The application encrypts sensitive data before storing:
- ✅ Client secrets are encrypted
- ✅ Access tokens are encrypted
- ✅ Refresh tokens are encrypted

## 🧪 Testing the Connection

Run this Python script to test your connection:

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# Test connection by fetching accounts
try:
    response = supabase.table('amazon_ads_accounts').select("*").execute()
    print("✅ Connection successful!")
    print(f"Found {len(response.data)} accounts")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## 📊 Database Schema

After setup, you'll have these tables:

### `amazon_ads_accounts`
- Stores Amazon Ads account configurations
- Client secrets are encrypted before storage

### `amazon_ads_tokens`
- Stores OAuth tokens (encrypted)
- One active token set per account
- Tracks expiration and refresh count

### `token_refresh_history`
- Audit log of all token operations
- Useful for debugging and monitoring

### `api_keys`
- API keys for programmatic access
- Hashed for security

## 🚨 Common Issues

### Issue: "permission denied to set parameter"
**Solution**: Use the `supabase_migration_simple.sql` file instead of the original. It doesn't try to set database parameters.

### Issue: "relation does not exist"
**Solution**: Make sure you're running the migration in the correct project. Check you're in the SQL Editor for the right project.

### Issue: "Connection refused" in application
**Solution**:
1. Check your SUPABASE_URL doesn't have trailing slashes
2. Verify you're using the service_role key, not the anon key
3. Ensure your project is not paused (free tier pauses after inactivity)

## 🔄 Updating the Schema

If you need to make changes later:

1. Create a new migration file
2. Use `IF NOT EXISTS` and `DROP ... IF EXISTS` to make it idempotent
3. Test in a development project first

Example migration:
```sql
-- Add a new column
ALTER TABLE amazon_ads_accounts
ADD COLUMN IF NOT EXISTS region VARCHAR(50) DEFAULT 'NA';
```

## 🎯 Next Steps

1. **Run the Application**:
   ```bash
   pip install -r requirements.txt
   uvicorn web_main:app --reload
   ```

2. **Access the Web Interface**:
   - Open http://localhost:8000
   - Click "Connect Amazon Account"
   - Follow the OAuth flow

3. **Deploy to Railway**:
   - Push to GitHub
   - Connect Railway to your repo
   - Add the same environment variables
   - Deploy!

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)

## 💡 Tips

1. **Monitor Usage**: Check the Database section in Supabase dashboard for usage stats
2. **Backups**: Supabase provides automatic backups (Pro plan) or download manual backups
3. **Performance**: The indexes are already created for optimal performance
4. **Logs**: Check the Logs section in Supabase for debugging

---

Need help? Check the logs in your Supabase dashboard or the application logs for detailed error messages.