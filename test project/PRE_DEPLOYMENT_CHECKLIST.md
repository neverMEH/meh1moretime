# Pre-Deployment Checklist for Railway

## ✅ Completed Tasks

### 1. ✅ Supabase Setup
- [x] Created Supabase project
- [x] Ran migration script (`supabase_migration_simple.sql`)
- [x] Tables created: amazon_ads_accounts, amazon_ads_tokens, token_refresh_history, api_keys

### 2. ✅ GitHub Repository
- [x] Code committed to GitHub: https://github.com/neverMEH/meh1moretime
- [x] Added .gitignore to exclude sensitive files
- [x] Pushed all necessary files

### 3. ✅ Environment Variables Prepared
- [x] Created `railway-variables.json` with all required configs
- [x] Generated encryption keys
- [x] Included Amazon Client ID and Secret

## 📋 Tasks You Need to Complete

### 4. ⚠️ Create Initial API Key in Supabase
Run this in your Supabase SQL Editor:

```sql
-- Option 1: Use the provided script
-- Copy contents of create_initial_api_key.sql
```

Or manually:

```sql
INSERT INTO api_keys (key_hash, name, permissions, is_active)
VALUES (
    encode(digest('your-chosen-api-key-here', 'sha256'), 'hex'),
    'Web Interface Key',
    '["read", "write", "web", "admin"]'::jsonb,
    true
);
```

**Note**: The web interface doesn't require API keys for normal operation, but having one is useful for API testing.

### 5. ⚠️ Update Amazon App Settings

Go to your Amazon Advertising API application settings and add these redirect URIs:

```
# For local development:
http://localhost:8000/callback

# For Railway (update with your actual domain after deployment):
https://your-app-name.up.railway.app/callback
https://meh1moretime-production.up.railway.app/callback
```

**Steps:**
1. Log into Amazon Developer Console
2. Go to your Advertising API app
3. Find "Allowed Return URLs" or "Redirect URIs"
4. Add the URLs above
5. Save changes

## 🚀 Ready for Railway Deployment

Once the above is complete, you're ready to deploy:

### 1. Connect Railway to GitHub
1. Go to [Railway](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Select `neverMEH/meh1moretime`

### 2. Add Environment Variables
1. Go to Variables tab
2. Click RAW Editor
3. Paste contents from `railway-variables.json`
4. **UPDATE** these values with your Railway URL:
   ```json
   "APP_URL": "https://YOUR-APP.up.railway.app"
   "ALLOWED_ORIGINS": "https://YOUR-APP.up.railway.app"
   ```

### 3. Deploy
Railway will automatically:
- Detect Python app
- Install dependencies from requirements.txt
- Run the web server with uvicorn
- Provide you with a URL

### 4. First Test
1. Visit your Railway URL
2. Click "Connect Amazon Account"
3. Enter your Amazon credentials
4. Complete OAuth flow
5. Check dashboard

## 🔍 Verification Steps

After deployment, verify:

- [ ] Homepage loads at your Railway URL
- [ ] "Connect Amazon Account" button works
- [ ] Can enter account details in modal
- [ ] OAuth redirect to Amazon works
- [ ] Callback returns successfully
- [ ] Tokens are stored in dashboard
- [ ] Token refresh works

## 🐛 Troubleshooting

### If Railway deployment fails:
1. Check Railway logs for specific errors
2. Verify all environment variables are set
3. Ensure you're using service_role key from Supabase

### If OAuth fails:
1. Check Amazon app redirect URIs include your Railway URL
2. Verify APP_URL environment variable matches your Railway domain
3. Check browser console for errors

### If database connection fails:
1. Verify Supabase project is active (not paused)
2. Check you ran the migration successfully
3. Ensure SUPABASE_KEY is the service_role key

## 📝 Important URLs

- **GitHub Repo**: https://github.com/neverMEH/meh1moretime
- **Supabase Project**: https://jfxnfryobrkgckcktymyw.supabase.co
- **Railway App**: Will be provided after deployment
- **Amazon Developer**: https://developer.amazon.com/apps-and-games/login

## 🎯 Final Steps

1. Deploy to Railway ✓
2. Update APP_URL with Railway domain
3. Test complete flow
4. Share your app URL!

---

**You're ready to deploy!** The application is fully prepared for Railway deployment.