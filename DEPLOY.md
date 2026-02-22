# HarvardTax Deployment Guide

## Prerequisites

- [Railway](https://railway.app) account
- [Supabase](https://supabase.com) project
- [Intuit Developer](https://developer.intuit.com) app (QuickBooks Online)
- [Anthropic](https://console.anthropic.com) API key

## 1. Supabase Setup

1. Create a new Supabase project
2. Go to **SQL Editor** and run the contents of `backend/schema.sql`
3. Note your **Project URL** and **anon/service key** from Settings → API

## 2. Railway Backend

1. Create a new project on Railway
2. Add a service → **GitHub Repo** → select this repo
3. Set the **Root Directory** to `backend`
4. Railway will auto-detect the `Dockerfile`
5. Add these **environment variables**:

| Variable | Value |
|---|---|
| `QBO_CLIENT_ID` | From Intuit developer portal |
| `QBO_CLIENT_SECRET` | From Intuit developer portal |
| `QBO_REDIRECT_URI` | `https://<backend-url>/api/qbo/callback` |
| `QBO_ENVIRONMENT` | `production` |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase service role key |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `FRONTEND_URL` | `https://<frontend-url>` (for CORS) |

6. Deploy and note the generated Railway URL

## 3. Railway Frontend

1. In the same Railway project, add another service from the same repo
2. Set the **Root Directory** to `frontend`
3. Add environment variables:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend Railway URL from step 2 |

4. Deploy

## 4. QuickBooks Production App

1. Go to [Intuit Developer Portal](https://developer.intuit.com)
2. Select your app → **Keys & credentials** → **Production**
3. Add the production redirect URI: `https://<backend-railway-url>/api/qbo/callback`
4. Note the production Client ID and Secret (update Railway env vars if different from sandbox)

## 5. Custom Domain

1. In Railway, select the **frontend** service
2. Go to **Settings** → **Networking** → **Custom Domain**
3. Add `harvardtax.com`
4. Configure your DNS:
   - Add a `CNAME` record pointing `harvardtax.com` to the Railway-provided domain
   - Or use an `A` record if Railway provides an IP
5. Wait for SSL certificate provisioning (automatic)

## 6. Post-Deploy Checklist

- [ ] Backend health check: `curl https://<backend-url>/health`
- [ ] Frontend loads: visit `https://harvardtax.com`
- [ ] QBO OAuth flow: click "Connect QuickBooks" and complete authorization
- [ ] PDF generation: run a tax estimate and download the PDF
- [ ] AI chat: test the AI tax assistant
- [ ] Check Railway logs for any errors

## Local Development

Use Docker Compose for local dev:

```bash
# Copy env file
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# Start both services
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

Or run services individually without Docker:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```
