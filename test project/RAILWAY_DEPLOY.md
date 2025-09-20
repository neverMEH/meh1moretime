# Railway Deployment Instructions

## 🚀 Quick Deploy to Railway

### Step 1: Import Variables to Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to the **Variables** tab
4. Click **RAW Editor**
5. Copy and paste everything from `railway-variables.json`
6. **IMPORTANT**: Update `APP_URL` with your actual Railway URL:
   - It will look like: `https://your-app-name.up.railway.app`
   - You can find this in Railway under Settings > Domains

### Step 2: Update the Variables

After pasting, make sure to update:

1. **APP_URL**: Replace with your actual Railway domain
   ```
   "APP_URL": "https://meh1moretime-production.up.railway.app"
   ```

2. **ALLOWED_ORIGINS**: Update with your Railway domain
   ```
   "ALLOWED_ORIGINS": "https://meh1moretime-production.up.railway.app"
   ```

### Step 3: Deploy

1. Railway will automatically deploy once variables are saved
2. Wait for the build to complete (usually 2-3 minutes)
3. Click on the generated domain to access your app

## 📋 Environment Variables Explained

| Variable | Description | Value |
|----------|-------------|-------|
| `SUPABASE_URL` | Your Supabase project URL | Already set |
| `SUPABASE_KEY` | Service role key (NOT anon key) | Already set |
| `ENCRYPTION_KEY` | Fernet key for token encryption | Auto-generated |
| `SESSION_SECRET` | Secret for web sessions | Auto-generated |
| `AMAZON_CLIENT_ID` | Your Amazon Ads API client ID | Already set |
| `AMAZON_CLIENT_SECRET` | Your Amazon Ads API client secret | Already set |
| `ENVIRONMENT` | Set to "production" for Railway | production |
| `APP_URL` | **UPDATE THIS** with your Railway URL | Need to update |
| `ALLOWED_ORIGINS` | CORS origins | Need to update |

## 🔧 Manual Setup in Railway UI

If you prefer to add variables manually:

1. Go to Variables tab in Railway
2. Click "Add Variable"
3. Add each variable one by one:

```
SUPABASE_URL = https://jfxnfryobrkgckcktymyw.supabase.co
SUPABASE_KEY = [your service role key]
ENCRYPTION_KEY = 8Gg4PjL_yBmQ-1GRZUo1QyGH4EWcGS1rCPOjKR-AoOI=
SESSION_SECRET = 4Ap5VSfkziC6a157PcmlkggDpDoseXbk_8FIriR6IJY
AMAZON_CLIENT_ID = amzn1.application-oa2-client.cf1789da23f74ee489e2373e424726af
AMAZON_CLIENT_SECRET = [your client secret]
ENVIRONMENT = production
APP_URL = https://[your-app].up.railway.app
ALLOWED_ORIGINS = https://[your-app].up.railway.app
```

## ✅ Verification

After deployment:

1. Visit your Railway URL
2. You should see the Amazon Ads Token Manager homepage
3. Click "Connect Amazon Account" to test the flow
4. Check Railway logs for any errors

## 🐛 Troubleshooting

### If you see "Service Unavailable":
- Check that all environment variables are set
- Verify SUPABASE_KEY is the service_role key, not anon key
- Check Railway logs for specific errors

### If OAuth redirect fails:
- Update APP_URL to match your Railway domain exactly
- Make sure Amazon app redirect_uri includes your Railway URL

### If database connection fails:
- Verify your Supabase project is active (not paused)
- Check that you ran the migration in Supabase SQL editor
- Ensure you're using the service_role key

## 🔒 Security Notes

- The `railway-variables.json` file contains sensitive keys
- **Do NOT commit this file to GitHub**
- Add it to `.gitignore`:
  ```bash
  echo "railway-variables.json" >> .gitignore
  ```

## 📱 After Deployment

1. Update your Amazon App settings:
   - Add your Railway URL to allowed redirect URIs
   - Format: `https://your-app.up.railway.app/callback`

2. Test the complete flow:
   - Connect an account
   - Authorize with Amazon
   - View tokens in dashboard

---

Need help? Check the Railway logs or Supabase logs for detailed error messages.