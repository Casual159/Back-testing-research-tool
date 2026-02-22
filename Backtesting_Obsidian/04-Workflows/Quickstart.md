# Quick Start Guide

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Anthropic API key (for AI agent)

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
# Edit .env with your credentials:
#   - PostgreSQL connection
#   - ANTHROPIC_API_KEY (required for AI agent)
#   - Binance API keys (optional, for recent data)

# 4. Database
createdb trading_bot

# 5. Frontend dependencies
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

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Features Overview

### AI Chat (/chat)
Natural language interface for strategy research. The agent guides you through:
1. **Strategy Design** - Discuss trading approach and parameters
2. **Validation** - Register strategy in the system
3. **Data Check** - Verify historical data availability
4. **Backtest** - Run backtests with proper validation
5. **Analysis** - Interpret results and get recommendations

### Strategies (/strategies)
- View all registered strategies
- Create new strategies (built-in variants or composite)
- Edit strategy parameters
- Delete strategies

### Backtest (/backtest)
- Configure backtest parameters
- Select date range and symbol
- Apply regime filters
- View live progress

### Results (/results)
- Browse saved backtest reports
- View detailed metrics and trade history
- Compare strategy performance

### Data Management (/data)
- Fetch historical OHLCV data from Binance
- View available data ranges
- Delete old data

### Charts (/chart)
- Interactive candlestick charts
- Technical indicators overlay
- Market regime visualization

---

## Environment Variables

```env
# PostgreSQL (Required)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_bot
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# AI Agent (Required for chat)
ANTHROPIC_API_KEY=your_anthropic_api_key

# Binance API (Optional - for recent data)
BINANCE_LIVE_API_KEY=
BINANCE_LIVE_API_SECRET=

# Trading Settings
TEST_MODE=true
INITIAL_CAPITAL=10000
MAX_POSITION_SIZE=0.2
```

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

### AI Agent not responding
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check API quota at console.anthropic.com
