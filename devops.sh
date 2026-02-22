#!/bin/bash

# DevOps CLI Wrapper for Railway Deployment Automation
# Usage: ./devops.sh <command> [args]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# =============================================================================
# COMMANDS
# =============================================================================

show_help() {
    echo -e "${BLUE}DevOps CLI - Railway Deployment Automation${NC}"
    echo ""
    echo "Usage: ./devops.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo ""
    echo -e "${GREEN}Deployment:${NC}"
    echo "  status [env]           - Show deployment status"
    echo "  deploy <env>           - Deploy to environment (staging/production)"
    echo "  logs [env] [lines]     - Show deployment logs"
    echo "  envs                   - List available environments"
    echo ""
    echo -e "${GREEN}Database:${NC}"
    echo "  migrate [revision]     - Run migrations (default: head)"
    echo "  db-status              - Show current migration revision"
    echo "  db-history             - Show migration history"
    echo "  db-check               - Check for pending migrations"
    echo ""
    echo -e "${GREEN}Monitoring:${NC}"
    echo "  health                 - Check API health"
    echo "  errors [limit]         - Show recent errors"
    echo "  analyze [limit]        - Analyze errors with AI"
    echo "  stats                  - Show database statistics"
    echo ""
    echo -e "${GREEN}MCP Server:${NC}"
    echo "  mcp                    - Start DevOps MCP server"
    echo ""
    echo "Examples:"
    echo "  ./devops.sh deploy staging"
    echo "  ./devops.sh logs production 200"
    echo "  ./devops.sh db-check"
    echo "  ./devops.sh analyze 50"
}

# Railway commands
cmd_status() {
    env=${1:-""}
    echo -e "${BLUE}Fetching deployment status...${NC}"
    if [ -n "$env" ]; then
        railway status -e "$env"
    else
        railway status
    fi
}

cmd_deploy() {
    env=$1
    if [ -z "$env" ]; then
        echo -e "${RED}Error: Environment required${NC}"
        echo "Usage: ./devops.sh deploy <staging|production>"
        exit 1
    fi

    echo -e "${YELLOW}Deploying to $env...${NC}"
    echo ""

    # Check for pending migrations
    echo -e "${BLUE}Checking for pending migrations...${NC}"
    alembic current

    # Deploy
    railway up -e "$env" --detach

    echo -e "${GREEN}Deployment started!${NC}"
    echo "Check status with: ./devops.sh status $env"
    echo "View logs with: ./devops.sh logs $env"
}

cmd_logs() {
    env=${1:-""}
    lines=${2:-100}

    echo -e "${BLUE}Fetching logs (last $lines lines)...${NC}"
    if [ -n "$env" ]; then
        railway logs -e "$env" --lines "$lines"
    else
        railway logs --lines "$lines"
    fi
}

cmd_envs() {
    echo -e "${BLUE}Available environments:${NC}"
    railway environment list
}

# Database commands
cmd_migrate() {
    revision=${1:-head}
    echo -e "${BLUE}Running migrations to $revision...${NC}"
    alembic upgrade "$revision"
    echo -e "${GREEN}Migrations complete!${NC}"
}

cmd_db_status() {
    echo -e "${BLUE}Current migration revision:${NC}"
    alembic current
}

cmd_db_history() {
    echo -e "${BLUE}Migration history:${NC}"
    alembic history
}

cmd_db_check() {
    echo -e "${BLUE}Checking for pending migrations...${NC}"
    alembic current
    echo ""
    echo -e "${BLUE}Latest revision:${NC}"
    alembic heads
}

# Monitoring commands (via API)
cmd_health() {
    echo -e "${BLUE}Checking API health...${NC}"
    curl -s http://localhost:8000/ | python -m json.tool
}

cmd_errors() {
    limit=${1:-100}
    echo -e "${BLUE}Fetching last $limit errors...${NC}"
    curl -s "http://localhost:8000/api/errors?limit=$limit" | python -m json.tool
}

cmd_analyze() {
    limit=${1:-100}
    echo -e "${BLUE}Analyzing errors (this may take a moment)...${NC}"

    # This would need a custom endpoint or use the MCP server
    # For now, just fetch errors
    curl -s "http://localhost:8000/api/errors?limit=$limit" | python -m json.tool

    echo ""
    echo -e "${YELLOW}Note: For AI analysis, use: ./devops.sh mcp${NC}"
    echo -e "${YELLOW}Then call monitor_analyze_errors tool${NC}"
}

cmd_stats() {
    echo -e "${BLUE}Fetching database statistics...${NC}"
    curl -s http://localhost:8000/api/data/stats | python -m json.tool
}

# MCP Server
cmd_mcp() {
    echo -e "${BLUE}Starting DevOps MCP Server...${NC}"
    echo -e "${YELLOW}Use with Claude Code or other MCP clients${NC}"
    echo ""
    python agent/devops_mcp_server.py
}

# =============================================================================
# MAIN
# =============================================================================

command=${1:-help}

case $command in
    # Deployment
    status)
        cmd_status "$2"
        ;;
    deploy)
        cmd_deploy "$2"
        ;;
    logs)
        cmd_logs "$2" "$3"
        ;;
    envs)
        cmd_envs
        ;;

    # Database
    migrate)
        cmd_migrate "$2"
        ;;
    db-status)
        cmd_db_status
        ;;
    db-history)
        cmd_db_history
        ;;
    db-check)
        cmd_db_check
        ;;

    # Monitoring
    health)
        cmd_health
        ;;
    errors)
        cmd_errors "$2"
        ;;
    analyze)
        cmd_analyze "$2"
        ;;
    stats)
        cmd_stats
        ;;

    # MCP
    mcp)
        cmd_mcp
        ;;

    # Help
    help|--help|-h)
        show_help
        ;;

    *)
        echo -e "${RED}Error: Unknown command '$command'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
