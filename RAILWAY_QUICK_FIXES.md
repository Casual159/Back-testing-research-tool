# Railway Quick Fixes - Common Issues

One-liner fixes for the most common Railway deployment problems.

---

## 🔥 TOP 5 Issues & Instant Fixes

### 1. "Health check failed" ❌

**Symptoms:** Deployment builds but crashes immediately.

**Fix:**
```bash
# Ensure PORT binding in railway.toml
echo 'startCommand = "uvicorn api.main:app --host 0.0.0.0 --port \$PORT"' >> railway.toml

# Increase timeout
railway variables set RAILWAY_HEALTHCHECK_TIMEOUT_SEC=100

# Redeploy
railway up --detach
```

---

### 2. "Database connection refused" 🔌

**Symptoms:** `psycopg2.OperationalError: could not connect`

**Fix:**
```bash
# Add PostgreSQL plugin first (via Railway dashboard)
# Then check variables:
railway variables | grep POSTGRES

# If missing, Railway should auto-set them when you add PostgreSQL plugin
# If not auto-set:
railway variables set POSTGRES_HOST=${{PGHOST}}
railway variables set POSTGRES_PORT=${{PGPORT}}
railway variables set POSTGRES_USER=${{PGUSER}}
railway variables set POSTGRES_PASSWORD=${{PGPASSWORD}}
railway variables set POSTGRES_DB=${{PGDATABASE}}
```

---

### 3. "ANTHROPIC_API_KEY not found" 🔑

**Symptoms:** App crashes with missing API key error.

**Fix:**
```bash
# Set the key
railway variables set ANTHROPIC_API_KEY=sk-ant-api03-...

# Verify
railway variables | grep ANTHROPIC

# Redeploy
railway up --detach
```

---

### 4. "Alembic migration failed" 📊

**Symptoms:** `alembic.util.exc.CommandError` during startup.

**Fix:**
```bash
# Check if migrations exist
ls alembic/versions/

# If empty, create initial migration locally:
alembic revision -m "initial tables" --autogenerate
git add alembic/versions/
git commit -m "Add initial migration"

# Then deploy
railway up --detach

# Or run migrations manually first:
railway run alembic upgrade head
```

---

### 5. "Build succeeded but app won't start" 🚀

**Symptoms:** Build completes but app immediately crashes.

**Quick diagnostic:**
```bash
# Check recent logs
railway logs --lines 100

# Common fixes:

# A) Missing dependencies
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
railway up --detach

# B) Wrong Python path
# Ensure railway.toml has:
startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
# NOT:
# startCommand = "python api/main.py"  ❌

# C) Check if health endpoint exists
curl https://your-app.railway.app/
# Should return JSON, not 404
```

---

## 🛠️ One-Line Diagnostics

```bash
# Check everything at once
./railway-setup.sh

# Or manually:

# 1. Check login
railway whoami

# 2. Check deployment status
railway status

# 3. Check variables (all required vars present?)
railway variables | grep -E "POSTGRES|ANTHROPIC"

# 4. Check logs for errors
railway logs --lines 50 | grep -i error

# 5. Check health endpoint
curl https://$(railway variables get RAILWAY_PUBLIC_DOMAIN)/

# 6. Test database connection
railway run python -c "from config.config import Config; print(f'DB: {Config.POSTGRES_HOST}')"
```

---

## 🎯 Environment Variable Quick Setup

**Copy-paste this entire block:**

```bash
# After adding PostgreSQL plugin to Railway, run:

# Required
railway variables set ANTHROPIC_API_KEY=your-key-here

# Optional (for Binance data fetching)
railway variables set BINANCE_TESTNET=false
railway variables set BINANCE_LIVE_API_KEY=your-binance-key
railway variables set BINANCE_LIVE_API_SECRET=your-binance-secret

# Verify all variables
railway variables

# Deploy
railway up --detach
```

---

## 🔧 Fix railway.toml Issues

**If your railway.toml is broken, replace with this:**

```toml
# Railway Configuration
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

**Apply:**
```bash
# Save the above to railway.toml
git add railway.toml
git commit -m "Fix Railway config"
railway up --detach
```

---

## 🚨 Emergency Rollback

**If deployment broke production:**

```bash
# Option 1: Redeploy previous working version
railway rollback

# Option 2: Revert git commit and redeploy
git revert HEAD
git push
railway up --detach

# Option 3: Use Railway dashboard
# Go to Deployments → Find last working deploy → Click "Redeploy"
```

---

## 📊 Check Migration Status

```bash
# Local
alembic current
alembic heads

# On Railway
railway run alembic current
railway run alembic heads

# If out of sync, force upgrade
railway run alembic upgrade head
```

---

## 🧪 Test Before Deploy

**Always test locally first:**

```bash
# 1. Start local server
./start-dev.sh

# 2. Test health endpoint
curl http://localhost:8000/

# 3. Test API endpoint
curl http://localhost:8000/api/data/stats

# 4. Check logs
# In another terminal, watch logs for errors

# 5. If all good, deploy
railway up --detach
```

---

## 💡 Quick Tips

### Fastest way to fix most issues:

1. **Run the setup script:**
   ```bash
   ./railway-setup.sh
   ```

2. **Check the logs:**
   ```bash
   railway logs --lines 100
   ```

3. **Follow the error message** - Railway logs usually tell you exactly what's wrong.

---

## 🔗 Need More Help?

- Full guide: [RAILWAY_TROUBLESHOOTING.md](RAILWAY_TROUBLESHOOTING.md:1)
- DevOps automation: [DEVOPS_AGENT_README.md](DEVOPS_AGENT_README.md:1)
- Database migrations: [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md:1)

---

## 🎯 Deployment Checklist (30 seconds)

```bash
✓ Railway CLI installed?     railway --version
✓ Logged in?                 railway whoami
✓ PostgreSQL plugin added?   (check dashboard)
✓ API key set?               railway variables | grep ANTHROPIC
✓ Code committed?            git status
✓ Local tests pass?          ./start-dev.sh && curl localhost:8000/

# All good? Deploy!
railway up --detach && railway logs --follow
```

---

**Most issues are fixed by:**
1. Adding PostgreSQL plugin via dashboard
2. Setting `ANTHROPIC_API_KEY` variable
3. Ensuring correct `startCommand` in railway.toml
4. Running `./railway-setup.sh` for validation

Good luck! 🚀
