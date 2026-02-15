# Railway Deployment Guide

Quick guide for deploying the Backtesting Research Tool to Railway.

---

## Prerequisites

- ✅ Railway account: https://railway.app
- ✅ Railway CLI installed: `brew install railway`
- ✅ GitHub repo pushed

---

## Quick Start (First Time)

### 1. Setup Railway Project

```bash
# Login to Railway
railway login

# Initialize project (in project root)
railway init
# → Create new project
# → Name: backtesting-research-tool

# Link to GitHub (optional but recommended)
railway link
```

### 2. Add PostgreSQL Database

**Via Dashboard:**
1. Go to Railway Dashboard → Your Project
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway auto-creates `DATABASE_URL` environment variable

**Via CLI:**
```bash
railway add postgresql
```

### 3. Set Environment Variables

**Via Dashboard:**
Railway Dashboard → Project → Variables → Add:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (for live trading data)
BINANCE_LIVE_API_KEY=your_key
BINANCE_LIVE_API_SECRET=your_secret

# Database (auto-set by PostgreSQL plugin, but you can override)
POSTGRES_HOST=containers-us-west-xxx.railway.app
POSTGRES_DB=railway
POSTGRES_USER=postgres
POSTGRES_PASSWORD=xxx

# Or use single DATABASE_URL (auto-set)
DATABASE_URL=postgresql://postgres:xxx@containers-us-west-xxx.railway.app/railway
```

**Via CLI:**
```bash
railway variables set ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Deploy

**Option A: Manual Deploy (CLI)**
```bash
railway up
```

**Option B: GitHub Auto-Deploy (Recommended)**
```bash
# Push to GitHub
git push origin main

# Railway automatically deploys on every push!
```

---

## Deployment Files

Railway uses these files (already created):

| File | Purpose |
|------|---------|
| `Procfile` | Tells Railway how to start the app |
| `railway.json` | Build and deploy configuration |
| `runtime.txt` | Python version |
| `requirements.txt` | Python dependencies |
| `alembic/` | Database migrations (auto-run on deploy) |

---

## Verify Deployment

### Check Logs
```bash
railway logs
```

### Check Deployment Status
```bash
railway status
```

### Get Public URL
```bash
railway domain
```

Or see it in Railway Dashboard → Deployments → Latest → "View Deployment"

---

## Post-Deployment Checks

### 1. Health Check
```bash
curl https://your-app.railway.app/
# Expected: {"status": "running", ...}
```

### 2. Database Connection
```bash
curl https://your-app.railway.app/api/data/stats
# Expected: List of available data
```

### 3. Check Migrations
```bash
railway run alembic current
# Expected: 3a8136333301 (baseline)
```

### 4. API Documentation
Open: `https://your-app.railway.app/docs`

---

## Database Migrations

### Migrations Run Automatically

On every deploy, Railway runs:
```bash
alembic upgrade head
```

This is configured in `Procfile` and `railway.json`.

### Manual Migration (if needed)
```bash
# Run command in Railway environment
railway run alembic upgrade head

# Check current migration
railway run alembic current

# Rollback one migration
railway run alembic downgrade -1
```

---

## Environment-Specific Config

### Development (Local)
```bash
./start-dev.sh
# Uses .env file
```

### Staging (Railway)
```bash
railway up --environment staging
# Uses Railway staging environment variables
```

### Production (Railway)
```bash
git push origin main
# Auto-deploys to production environment
```

---

## Common Tasks

### View Logs (Live)
```bash
railway logs --follow
```

### Restart Service
```bash
railway restart
```

### SSH into Container
```bash
railway run bash
```

### Run Database Query
```bash
railway run psql $DATABASE_URL
```

### Scale Resources
Railway Dashboard → Project → Settings → Resources

---

## Continuous Deployment Workflow

```
1. Make changes locally
   vim api/main.py

2. Test locally
   ./start-dev.sh

3. Commit
   git add .
   git commit -m "add feature"

4. Push to GitHub
   git push origin main

5. Railway auto-deploys
   (Watch in Dashboard or `railway logs`)

6. Verify
   curl https://your-app.railway.app/
```

---

## Troubleshooting

### Build Fails
```bash
# Check logs
railway logs --build

# Common issues:
# - Missing dependency in requirements.txt
# - Python version mismatch (check runtime.txt)
# - Invalid railway.json syntax
```

### Migration Fails
```bash
# Check migration status
railway run alembic current

# Check database connection
railway run psql $DATABASE_URL -c "SELECT version();"

# Manually run migrations
railway run alembic upgrade head
```

### App Won't Start
```bash
# Check startup logs
railway logs

# Common issues:
# - Missing environment variables
# - Database not connected
# - Import errors (missing dependencies)
```

### Database Connection Issues
```bash
# Verify DATABASE_URL is set
railway variables

# Test connection
railway run python -c "import psycopg2; print('DB OK')"
```

---

## Costs & Monitoring

### Free Tier
- $5 credit/month
- ~140 hours of runtime
- Enough for development/staging

### Monitor Usage
Railway Dashboard → Project → Usage

### Estimate Costs
- Backend 24/7: ~$10-15/month
- PostgreSQL: included in backend cost
- Total: ~$10-20/month for small project

---

## Rollback

### Rollback to Previous Deployment
Railway Dashboard → Deployments → Select Previous → "Redeploy"

Or via CLI:
```bash
# List deployments
railway deployments

# Rollback to specific deployment
railway rollback <deployment-id>
```

---

## Custom Domain (Optional)

```bash
# Add custom domain
railway domain add yourdomain.com

# Get DNS instructions
railway domain
```

Then add CNAME record:
```
CNAME: yourdomain.com → your-app.railway.app
```

---

## Multi-Environment Setup

### Create Staging Environment
Railway Dashboard → Project → New Environment → "staging"

### Deploy to Staging
```bash
# Switch to staging
railway environment staging

# Deploy
railway up

# Or link to specific branch
# staging environment auto-deploys from `develop` branch
```

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel (see VERCEL_DEPLOYMENT.md)
3. ✅ Setup monitoring (Sentry, Logtail)
4. ✅ Configure custom domain
5. ✅ Setup staging environment

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: GitHub Issues

---

## Quick Reference

```bash
# Deploy
railway up

# Logs
railway logs --follow

# Status
railway status

# Restart
railway restart

# Environment variables
railway variables

# Run command
railway run <command>

# Domain
railway domain
```
