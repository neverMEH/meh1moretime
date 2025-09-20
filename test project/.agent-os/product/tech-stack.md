# Technical Stack

## Core Technologies

- **Application Framework:** Python 3.11+ with FastAPI
- **Database System:** Supabase (PostgreSQL)
- **JavaScript Framework:** N/A (Backend API)
- **Import Strategy:** pip/requirements.txt
- **CSS Framework:** N/A (Backend API)
- **UI Component Library:** N/A (Backend API)
- **Fonts Provider:** N/A
- **Icon Library:** N/A

## Infrastructure

- **Application Hosting:** Railway
- **Database Hosting:** Supabase Cloud
- **Asset Hosting:** Railway Static Files
- **Deployment Solution:** Railway Auto-Deploy from GitHub

## Development Tools

- **Code Repository URL:** https://github.com/your-org/amazon-ads-token-manager
- **Testing Framework:** pytest 7.x
- **Linting:** black, flake8, mypy
- **Documentation:** Sphinx with autodoc
- **Package Manager:** pip/poetry

## Security & Dependencies

- **Database Client:** Supabase Python SDK
- **Web Framework:** FastAPI with Uvicorn
- **HTTP Client:** httpx (async support)
- **Validation:** Pydantic for data models
- **Authentication:** JWT tokens via python-jose
- **Environment:** python-dotenv for configuration
- **CORS:** FastAPI CORS middleware
- **Rate Limiting:** slowapi for API protection

## Railway Deployment Configuration

- **Build Command:** pip install -r requirements.txt
- **Start Command:** uvicorn main:app --host 0.0.0.0 --port $PORT
- **Health Check:** /health endpoint
- **Environment Variables:**
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `JWT_SECRET`
  - `AMAZON_CLIENT_ID`
  - `AMAZON_CLIENT_SECRET`