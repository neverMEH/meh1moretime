# Amazon Ads Token Manager - Supabase & Railway Edition

A production-ready OAuth2 token management API for Amazon Advertising, powered by Supabase database and deployed on Railway.

## 🚀 Architecture Overview

- **API Framework**: FastAPI with async support
- **Database**: Supabase (PostgreSQL with Row Level Security)
- **Deployment**: Railway with auto-scaling
- **Security**: Encrypted token storage, API key authentication
- **Features**: Multi-account support, automatic token refresh, audit logging

## 📋 Prerequisites

1. **Supabase Account**: [Sign up at supabase.com](https://supabase.com)
2. **Railway Account**: [Sign up at railway.app](https://railway.app)
3. **Amazon Advertising API Access**: Client ID and Secret from Amazon
4. **Python 3.11+**: For local development

## 🛠️ Setup Instructions

### 1. Supabase Setup

1. Create a new Supabase project
2. Run the schema migration:
   ```sql
   -- Copy contents of supabase_schema.sql to SQL Editor
   -- Execute the entire script
   ```
3. Get your credentials:
   - Project URL: `Settings > API > Project URL`
   - Anon Key: `Settings > API > Project API keys > anon public`

### 2. Railway Deployment

1. Fork or clone this repository
2. Connect Railway to your GitHub repo
3. Create a new Railway project
4. Add environment variables:
   ```bash
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ENCRYPTION_KEY=your_fernet_key  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   JWT_SECRET=your_jwt_secret
   ENVIRONMENT=production
   ```
5. Deploy! Railway will auto-detect and deploy

### 3. Local Development

```bash
# Clone the repository
git clone your-repo-url
cd amazon-ads-token-manager

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Run locally
uvicorn main:app --reload --port 8000
```

## 📚 API Documentation

Once deployed, access interactive API docs at:
- Swagger UI: `https://your-app.railway.app/docs`
- ReDoc: `https://your-app.railway.app/redoc`

### Authentication

All API endpoints require an API key in the Authorization header:
```bash
Authorization: Bearer your_api_key
```

### Core Endpoints

#### Create Account
```bash
POST /api/accounts
{
  "account_name": "My Amazon Account",
  "client_id": "amzn1.application-oa2-client.xxx",
  "client_secret": "your-secret",
  "redirect_uri": "https://localhost"
}
```

#### Get OAuth URL
```bash
GET /api/oauth/url/{account_id}
# Returns the authorization URL for user consent
```

#### Exchange Authorization Code
```bash
POST /api/accounts/{account_id}/authenticate
{
  "authorization_code": "code_from_oauth"
}
```

#### Get Access Token (Auto-refresh)
```bash
GET /api/accounts/{account_id}/token
# Returns valid access token, auto-refreshes if needed
```

#### Check Token Status
```bash
GET /api/accounts/{account_id}/status
# Returns token expiration and refresh status
```

## 🔒 Security Features

- **Encrypted Storage**: All tokens encrypted with Fernet symmetric encryption
- **API Key Authentication**: Bearer token authentication for all endpoints
- **Row Level Security**: Supabase RLS policies for data isolation
- **Audit Logging**: All token operations logged with timestamps
- **Auto-refresh Buffer**: Tokens refreshed 5 minutes before expiration
- **HTTPS Only**: Railway provides automatic SSL certificates

## 🗄️ Database Schema

### Tables

1. **amazon_ads_accounts**: Account configurations
2. **amazon_ads_tokens**: Active OAuth tokens
3. **token_refresh_history**: Audit trail
4. **api_keys**: API key management

### Key Features

- Automatic `updated_at` timestamps
- Cascade deletes for data integrity
- Indexed for performance
- UUID primary keys

## 🚦 Monitoring & Health

### Health Check
```bash
GET /health
# Returns service status and database connection
```

### Metrics to Monitor
- Token refresh rate
- API response times
- Failed authentication attempts
- Database connection pool

## 📦 Client Usage Example

```python
import httpx
import asyncio

class AmazonAdsClient:
    def __init__(self, api_base_url: str, api_key: str):
        self.base_url = api_base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def get_token(self, account_id: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/accounts/{account_id}/token",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def make_ads_api_call(self, account_id: str):
        token = await self.get_token(account_id)
        # Use token for Amazon Ads API calls
        headers = {"Authorization": f"Bearer {token}"}
        # Make your API call...

# Usage
async def main():
    client = AmazonAdsClient(
        api_base_url="https://your-app.railway.app",
        api_key="your_api_key"
    )
    token = await client.get_token("account_uuid")
    print(f"Got token: {token[:20]}...")

asyncio.run(main())
```

## 🔧 Environment Variables

### Required
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon or service key
- `ENCRYPTION_KEY`: Fernet key for token encryption
- `JWT_SECRET`: Secret for JWT operations

### Optional
- `PORT`: Server port (Railway sets automatically)
- `ENVIRONMENT`: development/staging/production
- `ALLOWED_ORIGINS`: CORS allowed origins

## 📊 Scaling & Performance

### Railway Auto-scaling
- Configure replicas in `railway.json`
- Automatic health checks and restarts
- Zero-downtime deployments

### Database Optimization
- Connection pooling via Supabase
- Indexed queries for performance
- Automatic cleanup of expired tokens

### Caching Strategy
- Tokens cached in memory during request lifecycle
- Refresh buffer prevents unnecessary API calls
- Connection reuse with httpx

## 🐛 Troubleshooting

### Common Issues

1. **Token Refresh Failures**
   - Check refresh token validity
   - Verify client credentials
   - Review error logs in Railway

2. **Database Connection Issues**
   - Verify Supabase credentials
   - Check connection limits
   - Review Supabase dashboard

3. **API Key Not Working**
   - Ensure key hasn't expired
   - Check permissions in database
   - Verify Authorization header format

## 📝 Development Workflow

1. **Local Development**
   ```bash
   # Run with hot reload
   uvicorn main:app --reload

   # Run tests
   pytest tests/

   # Format code
   black .
   ```

2. **Database Migrations**
   - Add new SQL to `migrations/` folder
   - Run via Supabase SQL editor
   - Update schema documentation

3. **Deployment**
   ```bash
   # Push to main branch
   git push origin main
   # Railway auto-deploys
   ```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📄 License

MIT License - See LICENSE file

## 🆘 Support

- GitHub Issues: Report bugs and feature requests
- Railway Dashboard: Monitor deployments
- Supabase Dashboard: Database administration

## 🔗 Quick Links

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Supabase Documentation](https://supabase.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Amazon Advertising API](https://advertising.amazon.com/API/docs)

---

Built with ❤️ for reliable Amazon Ads integration