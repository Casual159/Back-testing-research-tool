# Railway Deployment Troubleshooting Guide

Common issues and fixes for Railway deployment.

---

## 🚨 Common Deployment Errors

### 1. **"Application failed to respond to HTTP requests"**

**Symptoms:**
- Deployment builds successfully but health check fails
- Service shows as "crashed" or "unhealthy"

**Causes & Fixes:**

#### A) Port Binding Issue

Railway provides `$PORT` environment variable. Your app MUST bind to it.

**Fix in [railway.toml](railway.toml:10):**
```toml
startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
```

**Check your code binds to PORT:**
```python
# api/main.py
import os
port = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
```

#### B) Wrong Health Check Path

**Fix in [railway.toml](railway.toml:11):**
```toml
healthcheckPath = "/"  # Make sure this endpoint exists!
```

**Verify endpoint exists:**
```bash
# Check your API has this route
curl http://localhost:8000/
# Should return: {"status": "running", ...}
```

#### C) Health Check Timeout

If app takes long to start (migrations, etc.):

**Fix in [railway.toml](railway.toml:12-13):**
```toml
healthcheckTimeout = 100  # Increase from default 60s
restartPolicyMaxRetries = 10
```

---

### 2. **"Database connection failed"**

**Symptoms:**
- Error: `could not connect to server`
- Error: `connection refused`

**Fixes:**

#### A) PostgreSQL Plugin Not Added

**Solution:**
1. Go to Railway dashboard
2. Click `+ New` → `Database` → `Add PostgreSQL`
3. Railway auto-creates these variables:
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`

#### B) Wrong Variable Names

Railway PostgreSQL uses `DATABASE_URL` by default, but our app uses individual vars.

**Fix: Add to Railway variables:**
```bash
railway variables set POSTGRES_HOST=${{PGHOST}}
railway variables set POSTGRES_PORT=${{PGPORT}}
railway variables set POSTGRES_USER=${{PGUSER}}
railway variables set POSTGRES_PASSWORD=${{PGPASSWORD}}
railway variables set POSTGRES_DB=${{PGDATABASE}}
```

Or use `DATABASE_URL` directly in code.

#### C) Internal Network Connection

Railway services use internal network. Make sure you're using Railway's provided database URL, not `localhost`.

---

### 3. **"Migrations failed"**

**Symptoms:**
- Error: `alembic.util.exc.CommandError`
- Error: `Target database is not up to date`

**Fixes:**

#### A) No Migrations Directory

**Check:**
```bash
ls alembic/versions/
```

If empty:
```bash
# Create initial migration
alembic revision -m "initial" --autogenerate
git add alembic/versions/
git commit -m "Add initial migration"
railway up
```

#### B) Database Not Initialized

First deployment needs tables created.

**Fix: Railway automatically runs migrations in [railway.toml](railway.toml:10):**
```toml
startCommand = "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT"
```

#### C) Alembic Not Finding DB

**Check `alembic.ini`:**
```ini
# Should use environment variable, NOT hardcoded
sqlalchemy.url = postgresql://%(POSTGRES_USER)s:%(POSTGRES_PASSWORD)s@%(POSTGRES_HOST)s:%(POSTGRES_PORT)s/%(POSTGRES_DB)s
```

Or set in `env.py`:
```python
from config.config import Config
config.set_main_option("sqlalchemy.url",
    f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
)
```

---

### 4. **"Missing environment variables"**

**Symptoms:**
- Error: `ANTHROPIC_API_KEY not found`
- App crashes immediately after deploy

**Fix:**

```bash
# Set required variables
railway variables set ANTHROPIC_API_KEY=sk-ant-...

# Check all variables
railway variables

# Or use our helper script
./railway-setup.sh
```

**Required variables:**
- `POSTGRES_HOST` (auto-set by PostgreSQL plugin)
- `POSTGRES_PORT` (auto-set)
- `POSTGRES_DB` (auto-set)
- `POSTGRES_USER` (auto-set)
- `POSTGRES_PASSWORD` (auto-set)
- `ANTHROPIC_API_KEY` (you must set)

**Optional:**
- `BINANCE_LIVE_API_KEY`
- `BINANCE_LIVE_API_SECRET`
- `BINANCE_TESTNET=false`

---

### 5. **"Build failed" / Dependency Errors**

**Symptoms:**
- Error: `Could not find a version that satisfies the requirement`
- Error: `No module named 'xyz'`

**Fixes:**

#### A) Missing Dependencies

**Check [requirements.txt](requirements.txt:1-97):**
```bash
# Make sure all required packages are listed
grep -E "fastapi|uvicorn|alembic|psycopg2" requirements.txt
```

#### B) Conflicting Dependencies

```bash
# Regenerate clean requirements
pip freeze > requirements.txt
```

#### C) Wrong Python Version

Railway auto-detects Python version from `runtime.txt` or uses latest.

**Create `runtime.txt`:**
```
python-3.12
```

#### D) System Dependencies

Some packages need system libraries (e.g., PostgreSQL dev headers for psycopg2).

**Solution:** Use `psycopg2-binary` instead of `psycopg2`:
```txt
# requirements.txt
psycopg2-binary==2.9.11  # Already in your requirements.txt ✓
```

---

### 6. **"Deployment works but /api/* routes return 404"**

**Symptoms:**
- Root `/` works
- `/api/data/stats` returns 404

**Causes:**

#### A) Wrong Base Path in Railway

**Check if Railway adds a base path.** Usually not needed for Railway.

#### B) CORS Issues

Frontend can't reach API.

**Fix in [api/main.py](api/main.py:1):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔧 Quick Diagnostics

### Run Health Checks

```bash
# 1. Automated pre-flight checks
./railway-setup.sh

# 2. Manual checks
railway whoami          # Check login
railway status          # Check deployment status
railway logs --lines 50 # Check recent logs
railway variables       # Check environment variables
```

### Check Application Logs

```bash
# Last 100 lines
railway logs --lines 100

# Follow logs in real-time
railway logs --follow

# Filter for errors
railway logs | grep -i error
```

### Test Database Connection

```bash
# Run command in Railway environment
railway run python -c "
from config.config import Config
import psycopg2
conn = psycopg2.connect(
    host=Config.POSTGRES_HOST,
    port=Config.POSTGRES_PORT,
    database=Config.POSTGRES_DB,
    user=Config.POSTGRES_USER,
    password=Config.POSTGRES_PASSWORD
)
print('✓ Database connection successful')
conn.close()
"
```

### Run Migrations Manually

```bash
# Run migrations in Railway environment
railway run alembic upgrade head
```

---

## 📋 Pre-Deployment Checklist

Before deploying, verify:

- [ ] Railway CLI installed: `railway --version`
- [ ] Logged in: `railway whoami`
- [ ] Project linked: `railway status`
- [ ] PostgreSQL plugin added (check dashboard)
- [ ] Environment variables set: `railway variables`
- [ ] `railway.toml` exists with correct startCommand
- [ ] Health check endpoint works locally: `curl localhost:8000/`
- [ ] Requirements.txt includes all dependencies
- [ ] Alembic migrations created: `ls alembic/versions/`
- [ ] Code committed to git: `git status`

**Use our helper script:**
```bash
./railway-setup.sh
```

---

## 🚀 Deployment Workflow

### First Time Deployment

```bash
# 1. Setup and validate
./railway-setup.sh

# 2. Add PostgreSQL plugin (via dashboard)
# Railway Dashboard → + New → Database → PostgreSQL

# 3. Set API key
railway variables set ANTHROPIC_API_KEY=your-key

# 4. Deploy to staging
railway up -e staging --detach

# 5. Monitor
railway logs -e staging --follow

# 6. Test
curl https://your-app.railway.app/
curl https://your-app.railway.app/api/data/stats

# 7. If successful, deploy to production
railway up -e production --detach
```

### Subsequent Deployments

```bash
# Quick deploy
railway up --detach

# Or with our CLI
./devops.sh deploy staging
```

---

## 🐛 Debug Mode

Enable verbose logging for troubleshooting:

### 1. Add to Railway variables:
```bash
railway variables set LOG_LEVEL=DEBUG
railway variables set PYTHONUNBUFFERED=1
```

### 2. Update logging in code:
```python
# api/main.py
from core.logging_config import setup_logging

# Enable JSON logs for production
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=True  # Structured logs for Railway
)
```

### 3. Check logs:
```bash
railway logs --lines 200 | grep -i error
```

---

## 📞 Getting Help

### Railway Support

1. **Railway Discord:** https://discord.gg/railway
2. **Railway Docs:** https://docs.railway.app/
3. **Railway Status:** https://status.railway.app/

### Project-Specific

1. Check existing migrations: `./devops.sh db-history`
2. Check API health: `./devops.sh health`
3. Analyze errors: `./devops.sh analyze`

---

## 💡 Pro Tips

1. **Always test locally first:**
   ```bash
   ./start-dev.sh
   curl localhost:8000/
   ```

2. **Use staging before production:**
   ```bash
   railway up -e staging
   # Test thoroughly
   railway up -e production
   ```

3. **Monitor after deploy:**
   ```bash
   railway logs --follow
   # Watch for first 5 minutes
   ```

4. **Keep Railway CLI updated:**
   ```bash
   npm update -g @railway/cli
   ```

5. **Use our helper scripts:**
   ```bash
   ./railway-setup.sh   # Pre-flight checks
   ./devops.sh          # Deployment automation
   ```

---

## 🔗 Related Docs

- [DEVOPS_AGENT_README.md](DEVOPS_AGENT_README.md:1) - DevOps automation guide
- [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md:1) - Database migration guide
- [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md:1) - Local development setup

---

**Still having issues?** Run the diagnostic script:
```bash
./railway-setup.sh
```

It will check everything and guide you through fixes.
