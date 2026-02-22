# Backtesting Research Tool

**AI-Powered Cryptocurrency Trading Strategy Research Platform**

A comprehensive platform for researching, backtesting, and analyzing trading strategies with an integrated AI research agent.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (Next.js + React)                 │
│              http://localhost:3000                      │
│  - AI Chat Interface (research agent)                   │
│  - Strategy Management                                  │
│  - Backtest Results & Reports                           │
│  - Interactive Candlestick Charts                       │
└────────────────────────┬────────────────────────────────┘
                         │ REST API + Streaming
┌────────────────────────▼────────────────────────────────┐
│              Backend (FastAPI)                          │
│              http://localhost:8000                      │
│  - AI Agent with Claude (tool-calling)                  │
│  - Backtest Engine                                      │
│  - Strategy CRUD                                        │
│  - Market Regime Detection                              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Core Engine                                │
│  - Event-driven Backtesting                             │
│  - Technical Indicators (RSI, MACD, BB, MA, ATR)        │
│  - Market Regime Classification                         │
│  - Composable Strategy Framework                        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              PostgreSQL Database                        │
│  - OHLCV candles, strategies, backtest_reports          │
│  - market_regimes, conversations, suggestions           │
└─────────────────────────────────────────────────────────┘
```

---

## Features

### AI Research Agent
- Natural language interface for strategy research
- Guided workflow: Design → Validate → Backtest → Analyze
- Streaming responses with tool execution visibility
- Conversation history and context management

### Backtesting Engine
- Event-driven execution (no look-ahead bias)
- Built-in strategies: MA Crossover, RSI Reversal, Bollinger Bands, MACD Cross
- Composable strategy framework for custom logic
- Performance metrics: Sharpe ratio, max drawdown, win rate, profit factor

### Market Analysis
- Multi-dimensional regime detection (trend, volatility, momentum)
- Regime-aware strategy filtering
- Technical indicators with configurable parameters

### Data Management
- Hybrid data fetcher (Binance Public Data + API)
- Efficient bulk downloads (80%+ bandwidth savings)
- PostgreSQL storage with time-series optimization

### DevOps Automation
- **Railway deployment automation** - Deploy to staging/production with one command
- **AI-powered error analysis** - Claude analyzes production errors and suggests fixes
- **Database migration management** - Automated Alembic migrations
- **Health monitoring** - API health checks and log analysis
- **MCP integration** - Use with Claude Code for conversational DevOps

See [DEVOPS_AGENT_README.md](DEVOPS_AGENT_README.md:1) for details.

---

## Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials

# 2. Database
createdb trading_bot

# 3. Frontend dependencies (first time)
cd frontend && npm install && cd ..

# 4. Run
./start-dev.sh
```

**Frontend:** http://localhost:3000
**API Docs:** http://localhost:8000/docs

---

## Project Structure

```
Back-testing-research-tool/
├── api/                    # FastAPI backend
│   └── main.py             # All API endpoints
├── agent/                  # AI Research Agent
│   ├── core.py             # Claude agent implementation
│   ├── tools.py            # Agent tool definitions
│   └── mcp_server.py       # MCP server for Claude Code
├── frontend/               # Next.js UI
│   └── app/
│       ├── chat/           # AI chat interface
│       ├── strategies/     # Strategy management
│       ├── backtest/       # Backtest configuration
│       └── results/        # Results & reports
├── core/
│   ├── data/               # Data fetching & storage
│   ├── backtest/           # Backtest engine & strategies
│   └── indicators/         # Technical indicators
├── config/                 # Configuration
└── Backtesting_Obsidian/   # Project documentation (Obsidian)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + shadcn/ui + Tailwind |
| Charts | Plotly.js |
| Backend | FastAPI + Uvicorn |
| AI Agent | Anthropic Claude (claude-sonnet-4) |
| Database | PostgreSQL |
| Data Source | Binance Public Data |

---

## Environment Variables

```env
# Required
POSTGRES_HOST=localhost
POSTGRES_DB=trading_bot
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
BINANCE_LIVE_API_KEY=        # For recent data
BINANCE_LIVE_API_SECRET=
```

---

## Troubleshooting

```bash
# Port in use
lsof -ti:3000 | xargs kill
lsof -ti:8000 | xargs kill

# PostgreSQL not running (macOS)
brew services start postgresql@15

# Create database
createdb trading_bot
```

---

## Documentation

### Getting Started
- [QUICKSTART.md](QUICKSTART.md) - Detailed setup guide
- [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md:1) - Developer tools and best practices

### Deployment & DevOps
- [DEVOPS_AGENT_README.md](DEVOPS_AGENT_README.md:1) - DevOps automation with Railway
- [RAILWAY_QUICK_FIXES.md](RAILWAY_QUICK_FIXES.md:1) - 🔥 Common deployment issues & instant fixes
- [RAILWAY_TROUBLESHOOTING.md](RAILWAY_TROUBLESHOOTING.md:1) - Complete troubleshooting guide

### Database
- [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md:1) - Database migration guide

### Architecture
- [Backtesting_Obsidian/](Backtesting_Obsidian/) - Full project documentation
