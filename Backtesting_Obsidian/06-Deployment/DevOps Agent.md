# DevOps Agent - Railway Deployment Automation

AI-powered DevOps automation agent using Railway for deployment, with MCP (Model Context Protocol) integration for Claude Code.

## 🎯 Features

- **Railway Deployment** - Deploy to staging/production with one command
- **Database Migrations** - Automated Alembic migration management
- **Error Monitoring** - AI-powered error analysis using Claude
- **Health Checks** - Monitor API and deployment health
- **MCP Integration** - Use with Claude Code for conversational DevOps

---

## 📦 Installation

### 1. Prerequisites

```bash
# Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your Railway project
railway link
```

### 2. Python Dependencies

Already included in `requirements.txt`:

```txt
anthropic>=0.43.0
mcp>=1.9.0
httpx>=0.27.0
alembic>=1.14.0
```

### 3. Environment Variables

Add to your `.env`:

```bash
# Required for AI error analysis
ANTHROPIC_API_KEY=your_key_here

# Optional - API base URL (default: http://localhost:8000)
API_BASE_URL=http://localhost:8000
```

---

## 🚀 Quick Start

### Option 1: CLI Commands

```bash
# Make executable
chmod +x devops.sh

# Deploy to staging
./devops.sh deploy staging

# Check status
./devops.sh status staging

# View logs
./devops.sh logs staging 200

# Run migrations
./devops.sh migrate

# Check for errors
./devops.sh errors 50

# AI error analysis
./devops.sh analyze
```

### Option 2: MCP Server (with Claude Code)

```bash
# Start MCP server
./devops.sh mcp

# Or directly:
python agent/devops_mcp_server.py
```

Then use in Claude Code:

```
User: "Deploy to staging"

Claude: I'll deploy to staging. Let me check status first...
→ Uses railway_status tool
→ Uses railway_deploy tool
→ Reports results
```

---

## 🛠️ Available Commands

### Deployment

| Command | Description | Example |
|---------|-------------|---------|
| `status [env]` | Show deployment status | `./devops.sh status staging` |
| `deploy <env>` | Deploy to environment | `./devops.sh deploy production` |
| `logs [env] [lines]` | Show logs | `./devops.sh logs staging 200` |
| `envs` | List environments | `./devops.sh envs` |

### Database

| Command | Description | Example |
|---------|-------------|---------|
| `migrate [revision]` | Run migrations | `./devops.sh migrate head` |
| `db-status` | Current revision | `./devops.sh db-status` |
| `db-history` | Migration history | `./devops.sh db-history` |
| `db-check` | Check pending | `./devops.sh db-check` |

### Monitoring

| Command | Description | Example |
|---------|-------------|---------|
| `health` | API health check | `./devops.sh health` |
| `errors [limit]` | Recent errors | `./devops.sh errors 100` |
| `analyze [limit]` | AI error analysis | `./devops.sh analyze 50` |
| `stats` | Database stats | `./devops.sh stats` |

---

## 🤖 MCP Tools Reference

When using with Claude Code, these tools are available:

### Railway Tools

- `railway_status` - Get deployment status
- `railway_deploy` - Deploy to environment
- `railway_logs` - Fetch logs
- `railway_list_environments` - List environments

### Database Tools

- `db_migrate` - Run migrations
- `db_current` - Show current revision
- `db_history` - Show migration history
- `db_check_pending` - Check for pending migrations

### Monitoring Tools

- `monitor_health` - Check API health
- `monitor_errors` - Fetch recent errors
- `monitor_analyze_errors` - AI-powered error analysis
- `monitor_data_stats` - Database statistics

---

## 📋 Deployment Workflow

### Standard Deployment

```bash
# 1. Check for pending migrations
./devops.sh db-check

# 2. Run migrations locally first
./devops.sh migrate

# 3. Deploy to staging
./devops.sh deploy staging

# 4. Monitor logs
./devops.sh logs staging 200

# 5. Check health
./devops.sh health

# 6. If all good, deploy to production
./devops.sh deploy production
```

### With Claude Code (AI-Assisted)

```
User: "Deploy latest version to staging and check for errors"

Claude:
1. ✓ Checking pending migrations... None found
2. ✓ Deploying to staging... Started
3. ✓ Monitoring logs... No errors
4. ✓ Health check... Healthy
5. ✓ Error analysis... 2 minor warnings

Deployment successful! Staging is running v1.2.3
Ready to deploy to production?
```

---

## 🔧 Configuration

### Railway Configuration ([railway.toml](railway.toml:1-23))

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.staging]
[environments.staging.deploy]
healthcheckPath = "/"
```

**Key Points:**
- Migrations run automatically on deploy (`alembic upgrade head`)
- Health check on root endpoint
- Auto-restart on failure (max 10 retries)

### Environment Variables on Railway

Set these in Railway dashboard:

```bash
# Required
POSTGRES_HOST=your-railway-postgres-host
POSTGRES_PORT=5432
POSTGRES_DB=trading_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
ANTHROPIC_API_KEY=your-key

# Optional
BINANCE_TESTNET=false
BINANCE_LIVE_API_KEY=your-key
BINANCE_LIVE_API_SECRET=your-secret
```

---

## 🧪 Testing

### Test MCP Server Locally

```bash
# Start backend first
./start-dev.sh

# In another terminal, start MCP server
python agent/devops_mcp_server.py

# Test with MCP inspector (if available)
# or use Claude Code
```

### Test CLI Commands

```bash
# Check Railway connection
railway whoami

# Check database
./devops.sh db-status

# Check API
./devops.sh health

# Check migrations
./devops.sh db-check
```

---

## 🐛 Troubleshooting

### Railway CLI not found

```bash
npm install -g @railway/cli
railway login
railway link
```

### Alembic not found

```bash
pip install alembic
```

### API not reachable

```bash
# Start local dev server first
./start-dev.sh

# Or update API_BASE_URL in .env
```

### MCP Server errors

```bash
# Check dependencies
pip install anthropic mcp httpx

# Check environment variables
echo $ANTHROPIC_API_KEY

# Run with debugging
python agent/devops_mcp_server.py
```

---

## 📚 Architecture

```
agent/
├── devops_mcp_server.py     # MCP server (main entry point)
└── tools/
    ├── railway_tools.py      # Railway CLI wrapper
    ├── database_tools.py     # Alembic migrations
    └── monitoring_tools.py   # Error analysis + health checks

devops.sh                     # CLI wrapper
railway.toml                  # Railway configuration
```

**Data Flow:**

```
User/Claude Code
    ↓
MCP Server (devops_mcp_server.py)
    ↓
Tools (railway_tools, database_tools, monitoring_tools)
    ↓
Railway CLI / Alembic / API
```

---

## 🎯 Next Steps

1. **Setup Railway** - Link your project and configure environments
2. **Test Locally** - Run `./devops.sh mcp` and test with Claude Code
3. **Deploy** - Use `./devops.sh deploy staging` for first deployment
4. **Monitor** - Check logs and errors regularly
5. **Iterate** - Add more tools as needed (e.g., GitHub Actions, Sentry)

---

## 🔗 Resources

- [Railway Docs](https://docs.railway.app/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Claude Code](https://claude.ai/claude-code)

---

## 📝 Example Session

```bash
$ ./devops.sh deploy staging

🔵 Deploying to staging...

🔵 Checking for pending migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
No pending migrations found ✓

Deploying...
⠋ Building...
✓ Build complete
⠋ Deploying...
✓ Deployment complete

🟢 Deployment started!
Check status with: ./devops.sh status staging
View logs with: ./devops.sh logs staging

$ ./devops.sh status staging
{
  "status": "deployed",
  "version": "abc123",
  "url": "https://your-app.railway.app",
  "updated": "2024-02-15T10:30:00Z"
}

$ ./devops.sh logs staging 50
[2024-02-15 10:30:00] INFO - Starting server...
[2024-02-15 10:30:01] INFO - Connected to database
[2024-02-15 10:30:02] INFO - Server started on port 8000
...
```

---

## 💡 Pro Tips

1. **Always test on staging first** - Never deploy to production without testing
2. **Check migrations before deploy** - Use `./devops.sh db-check`
3. **Monitor logs after deploy** - Watch for errors in first 5 minutes
4. **Use AI analysis** - Let Claude identify patterns in errors
5. **Automate with Claude Code** - Create custom deployment workflows

---

## 🤝 Contributing

This is part of the Backtesting Research Tool project. See main [README.md](README.md:1) for details.

---

**Built with ❤️ using Railway, Claude, and MCP**
