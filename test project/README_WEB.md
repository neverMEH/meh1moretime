# Amazon Ads Token Manager - Web Interface

A complete web-based OAuth2 token management system for Amazon Advertising API with a beautiful UI and seamless user experience.

## 🎯 Features

### User-Friendly Web Interface
- **One-Click Connect**: Simple "Connect Amazon Account" button to start OAuth flow
- **Visual Dashboard**: See all accounts and token status at a glance
- **Real-time Updates**: Auto-refresh token status every 30 seconds
- **No Technical Knowledge Required**: Guides users through the entire process

### Complete OAuth Flow
1. User enters Amazon Ads credentials in web form
2. Clicks authorize and is redirected to Amazon
3. Returns to callback page with automatic token exchange
4. Tokens stored securely in Supabase

### Dashboard Features
- View all connected accounts
- See token expiration status (Active/Expiring/Expired)
- One-click token refresh
- Copy access tokens to clipboard
- Download tokens as JSON
- Account statistics overview

## 🚀 Quick Start

### 1. Setup Supabase

```sql
-- Run supabase_schema.sql in your Supabase SQL editor
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your values
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ENCRYPTION_KEY=your_fernet_key
APP_URL=https://your-app.railway.app
```

### 3. Deploy to Railway

```bash
# Push to GitHub
git push origin main

# Railway will auto-deploy
# Set environment variables in Railway dashboard
```

### 4. Access Your App

Navigate to `https://your-app.railway.app`

## 📱 User Flow

### First-Time Setup

1. **Visit Homepage**
   - User sees clean landing page with benefits
   - Clicks "Connect Amazon Account"

2. **Enter Credentials**
   - Modal appears with form
   - User enters:
     - Account Name (friendly identifier)
     - Client ID (from Amazon)
     - Client Secret (encrypted before storage)
   - Clicks "Create Account"

3. **Authorize with Amazon**
   - Success modal shows
   - User clicks "Authorize with Amazon"
   - Redirected to Amazon login

4. **Grant Permissions**
   - User logs into Amazon
   - Grants app permissions
   - Redirected back to callback page

5. **Automatic Token Exchange**
   - App automatically exchanges code for tokens
   - Shows success message
   - Redirects to dashboard

### Dashboard Usage

- **View All Accounts**: See status of all connected accounts
- **Check Token Status**: Visual indicators for Active/Expiring/Expired
- **Refresh Tokens**: One-click refresh before expiration
- **Get Access Token**: Copy token for API usage
- **Download Tokens**: Export as JSON for backup

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Web Browser   │────▶│   FastAPI    │────▶│  Supabase   │
│   (HTML/JS)     │◀────│   Backend    │◀────│  Database   │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                      │
         │                      ▼
         │              ┌──────────────┐
         └─────────────▶│ Amazon OAuth │
                        └──────────────┘
```

### Frontend Stack
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with animations
- **Vanilla JavaScript**: No framework dependencies
- **Font Awesome**: Icons
- **Responsive Design**: Mobile-friendly

### Backend Stack
- **FastAPI**: Async Python web framework
- **Jinja2**: Template rendering
- **Session Management**: Secure cookie-based sessions
- **Supabase SDK**: Database operations
- **Cryptography**: Token encryption

## 🔒 Security Features

- **Encrypted Storage**: All tokens encrypted with Fernet
- **Secure Sessions**: HTTPOnly cookies with CSRF protection
- **HTTPS Only**: Enforced in production
- **No Client Secrets**: Never exposed to browser
- **Auto Token Refresh**: Prevents expired token usage

## 📦 File Structure

```
project/
├── templates/              # HTML templates
│   ├── index.html         # Landing page
│   ├── dashboard.html     # Account dashboard
│   └── callback.html      # OAuth callback
├── static/                # Static assets
│   ├── styles.css        # Styling
│   ├── app.js            # Homepage JS
│   └── dashboard.js      # Dashboard JS
├── web_main.py           # FastAPI web application
├── supabase_token_manager.py  # Token management
└── requirements.txt      # Dependencies
```

## 🌐 Environment Variables

```bash
# Required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_key
ENCRYPTION_KEY=your_fernet_key

# Optional
APP_URL=http://localhost:8000  # Your app URL
SESSION_SECRET=auto_generated  # Session encryption
ENVIRONMENT=development         # or production
PORT=8000                      # Server port
```

## 🚦 API Endpoints (Web)

### Pages
- `GET /` - Landing page with connect form
- `GET /dashboard` - Account dashboard
- `GET /callback` - OAuth callback handler

### Web API
- `POST /web/accounts` - Create new account
- `GET /web/accounts` - List all accounts with status
- `GET /web/oauth/{account_id}` - Get OAuth URL
- `POST /web/callback` - Process OAuth callback
- `GET /web/accounts/{account_id}/token` - Get access token
- `POST /web/accounts/{account_id}/refresh` - Refresh token

## 🎨 Customization

### Branding
Edit `static/styles.css`:
```css
:root {
    --primary-color: #FF9900;  /* Amazon orange */
    --secondary-color: #232F3E; /* Amazon navy */
}
```

### Add Your Logo
Replace in `templates/index.html`:
```html
<div class="nav-brand">
    <img src="/static/logo.png" alt="Your Logo">
    <span>Your Company Name</span>
</div>
```

## 📱 Mobile Support

The interface is fully responsive:
- **Desktop**: Full dashboard with side-by-side cards
- **Tablet**: Stacked layout with touch-friendly buttons
- **Mobile**: Single column with larger tap targets

## 🐛 Troubleshooting

### Common Issues

1. **"Service not initialized" Error**
   - Check Supabase credentials
   - Verify environment variables are set

2. **OAuth Redirect Issues**
   - Ensure redirect_uri matches Amazon app settings
   - Update APP_URL environment variable

3. **Session Expired**
   - Sessions last 24 hours
   - User needs to refresh page

## 🚀 Production Deployment

### Railway Deployment

1. **Connect Repository**
   ```bash
   # In Railway dashboard
   - New Project > Deploy from GitHub
   - Select your repository
   ```

2. **Set Environment Variables**
   - Add all required variables in Railway dashboard
   - Set ENVIRONMENT=production

3. **Configure Domain**
   - Railway provides subdomain
   - Or add custom domain

4. **Update OAuth Settings**
   - Change redirect_uri in Amazon app
   - Update APP_URL in Railway

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "web_main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Monitoring

### Health Check
```bash
curl https://your-app.railway.app/health
```

### Session Metrics
- Active sessions shown in health endpoint
- Automatic cleanup every hour

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📄 License

MIT License

## 🆘 Support

- **Documentation**: See `/docs` endpoint for API docs
- **Issues**: GitHub Issues
- **Dashboard**: Railway/Supabase dashboards

---

Built for simplicity and security. Perfect for agencies and developers who need reliable Amazon Ads token management without the complexity.