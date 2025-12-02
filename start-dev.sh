#!/bin/bash

# Start Development Environment for Backtesting Research Tool

echo "🚀 Starting Backtesting Research Tool Development Environment"
echo ""

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start FastAPI backend in background
echo "🐍 Starting FastAPI backend on http://localhost:8000"
cd api
python main.py &
FASTAPI_PID=$!
cd ..

# Wait for FastAPI to start
sleep 2

# Start Next.js frontend
echo "⚛️  Starting Next.js frontend on http://localhost:3000"
cd frontend
npm run dev &
NEXTJS_PID=$!
cd ..

echo ""
echo "✅ Development environment started!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user interrupt
trap "kill $FASTAPI_PID $NEXTJS_PID; exit" INT
wait
