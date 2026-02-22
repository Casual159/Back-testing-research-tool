#!/bin/bash

# Railway Setup & Deployment Helper
# Validates configuration and helps with first deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Railway Deployment Setup & Validator       ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo ""

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

echo -e "${CYAN}[1/6] Pre-flight checks...${NC}"

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}✗ Railway CLI not found${NC}"
    echo -e "${YELLOW}  Install: npm install -g @railway/cli${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Railway CLI installed${NC}"

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo -e "${RED}✗ Not logged in to Railway${NC}"
    echo -e "${YELLOW}  Run: railway login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Logged in to Railway${NC}"

# Check if project is linked
if ! railway status &> /dev/null; then
    echo -e "${YELLOW}⚠ Project not linked to Railway${NC}"
    echo -e "${YELLOW}  Creating new project or link existing one?${NC}"
    read -p "  [n]ew project or [l]ink existing? (n/l): " choice

    if [ "$choice" = "n" ]; then
        echo -e "${BLUE}Creating new Railway project...${NC}"
        railway init
    else
        echo -e "${BLUE}Link to existing project...${NC}"
        railway link
    fi
fi
echo -e "${GREEN}✓ Project linked${NC}"
echo ""

# =============================================================================
# ENVIRONMENT VARIABLES CHECK
# =============================================================================

echo -e "${CYAN}[2/6] Checking environment variables...${NC}"

REQUIRED_VARS=(
    "POSTGRES_HOST"
    "POSTGRES_PORT"
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "ANTHROPIC_API_KEY"
)

OPTIONAL_VARS=(
    "BINANCE_TESTNET"
    "BINANCE_LIVE_API_KEY"
    "BINANCE_LIVE_API_SECRET"
)

missing_vars=0

# Check Railway environment variables
echo -e "${BLUE}Checking Railway environment variables...${NC}"

for var in "${REQUIRED_VARS[@]}"; do
    if railway variables get "$var" &> /dev/null; then
        echo -e "${GREEN}✓ $var${NC}"
    else
        echo -e "${RED}✗ $var (REQUIRED)${NC}"
        missing_vars=$((missing_vars + 1))
    fi
done

for var in "${OPTIONAL_VARS[@]}"; do
    if railway variables get "$var" &> /dev/null; then
        echo -e "${GREEN}✓ $var${NC}"
    else
        echo -e "${YELLOW}⚠ $var (optional)${NC}"
    fi
done

if [ $missing_vars -gt 0 ]; then
    echo ""
    echo -e "${RED}Missing $missing_vars required variables!${NC}"
    echo -e "${YELLOW}Set them with:${NC}"
    echo -e "${YELLOW}  railway variables set POSTGRES_HOST=<your-postgres-host>${NC}"
    echo -e "${YELLOW}  railway variables set POSTGRES_PASSWORD=<your-password>${NC}"
    echo -e "${YELLOW}  railway variables set ANTHROPIC_API_KEY=<your-key>${NC}"
    echo ""
    read -p "Do you want to set them now? (y/n): " set_vars

    if [ "$set_vars" = "y" ]; then
        echo ""
        echo -e "${BLUE}Setting environment variables...${NC}"

        # Check if Railway PostgreSQL plugin is added
        echo -e "${YELLOW}Do you have Railway PostgreSQL plugin added?${NC}"
        echo -e "${YELLOW}If yes, Railway auto-sets POSTGRES_* variables.${NC}"
        read -p "Have PostgreSQL plugin? (y/n): " has_pg

        if [ "$has_pg" != "y" ]; then
            echo ""
            echo -e "${YELLOW}Add PostgreSQL plugin first:${NC}"
            echo -e "${YELLOW}1. Go to Railway dashboard${NC}"
            echo -e "${YELLOW}2. Click '+ New' → 'Database' → 'PostgreSQL'${NC}"
            echo -e "${YELLOW}3. Railway will auto-configure POSTGRES_* variables${NC}"
            echo ""
            exit 1
        fi

        # Set ANTHROPIC_API_KEY
        read -p "Enter ANTHROPIC_API_KEY: " api_key
        if [ -n "$api_key" ]; then
            railway variables set "ANTHROPIC_API_KEY=$api_key"
            echo -e "${GREEN}✓ Set ANTHROPIC_API_KEY${NC}"
        fi

        # Optional: Binance
        read -p "Set Binance API credentials? (y/n): " set_binance
        if [ "$set_binance" = "y" ]; then
            read -p "Enter BINANCE_LIVE_API_KEY: " binance_key
            read -p "Enter BINANCE_LIVE_API_SECRET: " binance_secret

            railway variables set "BINANCE_LIVE_API_KEY=$binance_key"
            railway variables set "BINANCE_LIVE_API_SECRET=$binance_secret"
            railway variables set "BINANCE_TESTNET=false"
            echo -e "${GREEN}✓ Set Binance credentials${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping variable setup. Set them manually later.${NC}"
    fi
fi
echo ""

# =============================================================================
# DATABASE CHECK
# =============================================================================

echo -e "${CYAN}[3/6] Checking database migrations...${NC}"

# Check local migrations
if [ ! -d "alembic" ]; then
    echo -e "${RED}✗ Alembic not initialized${NC}"
    echo -e "${YELLOW}  Run: alembic init alembic${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Alembic initialized${NC}"

# Check for migration files
migration_count=$(ls alembic/versions/*.py 2>/dev/null | wc -l)
if [ "$migration_count" -eq 0 ]; then
    echo -e "${YELLOW}⚠ No migration files found${NC}"
    echo -e "${YELLOW}  This is OK for first deployment${NC}"
else
    echo -e "${GREEN}✓ Found $migration_count migration file(s)${NC}"
fi

# Check alembic.ini
if [ -f "alembic.ini" ]; then
    echo -e "${GREEN}✓ alembic.ini exists${NC}"
else
    echo -e "${RED}✗ alembic.ini not found${NC}"
    exit 1
fi
echo ""

# =============================================================================
# RAILWAY.TOML VALIDATION
# =============================================================================

echo -e "${CYAN}[4/6] Validating railway.toml...${NC}"

if [ ! -f "railway.toml" ]; then
    echo -e "${RED}✗ railway.toml not found${NC}"
    exit 1
fi

# Check for required fields
if grep -q "buildCommand" railway.toml; then
    echo -e "${GREEN}✓ buildCommand configured${NC}"
else
    echo -e "${YELLOW}⚠ No buildCommand in railway.toml${NC}"
fi

if grep -q "startCommand" railway.toml; then
    echo -e "${GREEN}✓ startCommand configured${NC}"

    # Check if migrations are in startCommand
    if grep -q "alembic upgrade head" railway.toml; then
        echo -e "${GREEN}✓ Auto-migrations enabled${NC}"
    else
        echo -e "${YELLOW}⚠ Migrations not in startCommand${NC}"
        echo -e "${YELLOW}  Consider adding: alembic upgrade head &&${NC}"
    fi
else
    echo -e "${RED}✗ No startCommand in railway.toml${NC}"
fi

if grep -q "healthcheckPath" railway.toml; then
    echo -e "${GREEN}✓ Health check configured${NC}"
else
    echo -e "${YELLOW}⚠ No health check configured${NC}"
fi
echo ""

# =============================================================================
# DEPENDENCIES CHECK
# =============================================================================

echo -e "${CYAN}[5/6] Checking dependencies...${NC}"

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ requirements.txt exists${NC}"

# Check for key packages
required_packages=("fastapi" "uvicorn" "alembic" "psycopg2-binary" "anthropic")

for pkg in "${required_packages[@]}"; do
    if grep -q "^$pkg" requirements.txt; then
        echo -e "${GREEN}✓ $pkg${NC}"
    else
        echo -e "${RED}✗ $pkg not in requirements.txt${NC}"
    fi
done
echo ""

# =============================================================================
# DEPLOYMENT READINESS
# =============================================================================

echo -e "${CYAN}[6/6] Deployment readiness check...${NC}"

echo -e "${BLUE}Checking Railway service status...${NC}"
railway status || true
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Pre-flight checks complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""

# =============================================================================
# DEPLOYMENT OPTIONS
# =============================================================================

echo -e "${BLUE}What would you like to do?${NC}"
echo ""
echo "  1) Deploy to staging"
echo "  2) Deploy to production"
echo "  3) Show deployment logs"
echo "  4) Run database migrations only"
echo "  5) Show environment variables"
echo "  6) Exit"
echo ""
read -p "Choose option (1-6): " option

case $option in
    1)
        echo -e "${BLUE}Deploying to staging...${NC}"
        railway up -e staging --detach
        echo -e "${GREEN}Deployment started!${NC}"
        echo -e "${YELLOW}Monitor with: railway logs -e staging${NC}"
        ;;
    2)
        echo -e "${YELLOW}⚠ Deploying to PRODUCTION${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo -e "${BLUE}Deploying to production...${NC}"
            railway up -e production --detach
            echo -e "${GREEN}Deployment started!${NC}"
            echo -e "${YELLOW}Monitor with: railway logs -e production${NC}"
        else
            echo -e "${YELLOW}Deployment cancelled${NC}"
        fi
        ;;
    3)
        echo -e "${BLUE}Fetching logs...${NC}"
        railway logs --lines 100
        ;;
    4)
        echo -e "${BLUE}Running migrations...${NC}"
        railway run alembic upgrade head
        echo -e "${GREEN}Migrations complete!${NC}"
        ;;
    5)
        echo -e "${BLUE}Environment variables:${NC}"
        railway variables
        ;;
    6)
        echo -e "${BLUE}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
