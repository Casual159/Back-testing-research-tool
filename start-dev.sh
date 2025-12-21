#!/bin/bash

# Start Development Environment for Backtesting Research Tool

set -e  # Exit on error

BACKEND_PORT=8000
FRONTEND_PORT=3000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  Backtesting Research Tool - Dev Server"
echo "=========================================="
echo ""

# =============================================================================
# CLEANUP - Kill existing processes on ports
# =============================================================================

cleanup_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Killing existing processes on port $port...${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

echo "Cleaning up existing processes..."
cleanup_port $BACKEND_PORT
cleanup_port $FRONTEND_PORT
echo -e "${GREEN}Ports $BACKEND_PORT and $FRONTEND_PORT are free${NC}"
echo ""

# =============================================================================
# CHECKS - Verify environment
# =============================================================================

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found.${NC}"
    echo "Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Python dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check if Node modules exist
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example${NC}"
    cp .env.example .env
    echo "Please edit .env with your credentials"
fi

# =============================================================================
# START SERVERS
# =============================================================================

# Start FastAPI backend
echo ""
echo "Starting FastAPI backend on http://localhost:$BACKEND_PORT..."
cd api
python main.py &
FASTAPI_PID=$!
cd ..

# Wait and verify backend is running
sleep 2
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo -e "${RED}Failed to start backend!${NC}"
    exit 1
fi

# Health check for backend
for i in {1..10}; do
    if curl -s http://localhost:$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is ready${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${YELLOW}Backend health check timed out (may still be starting)${NC}"
    fi
    sleep 1
done

# Start Next.js frontend
echo ""
echo "Starting Next.js frontend on http://localhost:$FRONTEND_PORT..."
cd frontend
npm run dev &
NEXTJS_PID=$!
cd ..

# Wait and verify frontend is running
sleep 3
if ! kill -0 $NEXTJS_PID 2>/dev/null; then
    echo -e "${RED}Failed to start frontend!${NC}"
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

# =============================================================================
# READY
# =============================================================================

echo ""
echo -e "${GREEN}=========================================="
echo "  Development environment started!"
echo "==========================================${NC}"
echo ""
echo "  Frontend:  http://localhost:$FRONTEND_PORT"
echo "  Backend:   http://localhost:$BACKEND_PORT"
echo "  API Docs:  http://localhost:$BACKEND_PORT/docs"
echo ""
echo "  Press Ctrl+C to stop all servers"
echo ""

# =============================================================================
# SHUTDOWN HANDLER
# =============================================================================

shutdown() {
    echo ""
    echo "Shutting down..."
    kill $FASTAPI_PID 2>/dev/null
    kill $NEXTJS_PID 2>/dev/null
    cleanup_port $BACKEND_PORT
    cleanup_port $FRONTEND_PORT
    echo -e "${GREEN}All servers stopped${NC}"
    exit 0
}

trap shutdown INT TERM

# Keep script running
wait
