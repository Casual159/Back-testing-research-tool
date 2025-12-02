# 🚀 Quick Start Guide

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+

## Setup

```bash
# 1. Clone & enter directory
cd Back-testing-research-tool

# 2. Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 4. Database
createdb trading_bot

# 5. Install frontend dependencies (first time only)
cd frontend
npm install
cd ..
```

## Running

### Automatic (Recommended)
```bash
./start-dev.sh
```

### Manual (2 terminals)
```bash
# Terminal 1: Backend
source venv/bin/activate
cd api
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

## URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Troubleshooting

### Port already in use
```bash
lsof -ti:3000 | xargs kill  # Frontend
lsof -ti:8000 | xargs kill  # Backend
```

### PostgreSQL not running
```bash
# macOS
brew services start postgresql@15

# Check status
brew services list
```

### Database not found
```bash
createdb trading_bot
```

### Frontend build errors
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

---

## Environment Variables (.env)

```env
# PostgreSQL (Required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_bot
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Binance API (Optional - for recent data)
BINANCE_LIVE_API_KEY=
BINANCE_LIVE_API_SECRET=

# Trading Settings
TEST_MODE=true
INITIAL_CAPITAL=10000
MAX_POSITION_SIZE=0.2
```

---

## What's Implemented

Check the GUI at http://localhost:3000 to see active features.

Current functionality:
- Data fetching from Binance Public Data
- PostgreSQL storage
- Interactive candlestick charts
- Symbol/timeframe selection
