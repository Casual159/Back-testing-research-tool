# Backtesting Research Tool

**Cryptocurrency Trading Strategy Research Platform**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│         Frontend (Next.js + React)              │
│         http://localhost:3000                   │
│  - Interactive charts (Plotly.js)               │
│  - Data management UI                           │
└──────────────────┬──────────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────────┐
│         Backend (FastAPI)                       │
│         http://localhost:8000                   │
│  - Data fetch endpoints                         │
│  - Chart data API                               │
└──────────────────┬──────────────────────────────┘
                   │ Python imports
┌──────────────────▼──────────────────────────────┐
│         Core Data Layer                         │
│  - BinanceBulkFetcher (data.binance.vision)     │
│  - PostgresStorage (candles table)              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         PostgreSQL Database                     │
│  - Historical OHLCV data                        │
└─────────────────────────────────────────────────┘
```

### Active Components
- **Data fetching & storage** - Binance Public Data → PostgreSQL
- **FastAPI backend** - REST endpoints for data operations
- **React frontend** - Interactive candlestick charts & data management

### Reference Code (Legacy)
- `core/backtest/` - Event-driven backtest engine patterns
- `core/indicators/` - Technical indicator implementations
- `core/backtest/strategies/` - Strategy composition patterns

These provide design patterns from [CryptoAnalyzer](https://github.com/Casual159/CryptoAnalyzer) for future implementation.

---

## 🚀 Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 2. Database
createdb trading_bot

# 3. Run (starts both backend + frontend)
./start-dev.sh
```

**Open:** http://localhost:3000
**API Docs:** http://localhost:8000/docs

---

## 📁 Project Structure

```
Back-testing-research-tool/
├── api/                    # FastAPI backend (port 8000)
│   └── main.py
├── frontend/              # Next.js UI (port 3000)
│   ├── app/
│   └── components/
├── core/
│   ├── data/              # Active: Data layer
│   │   ├── bulk_fetcher.py
│   │   ├── storage.py
│   │   └── fetcher.py
│   ├── backtest/          # Reference: Legacy patterns
│   └── indicators/        # Reference: Legacy patterns
├── config/                # Configuration
└── start-dev.sh          # Dev startup script
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + shadcn/ui |
| Charts | Plotly.js |
| Backend | FastAPI + Uvicorn |
| Database | PostgreSQL |
| Data Source | Binance Public Data |

---

## 💡 Design Decisions

### Hybrid Data Fetcher
**Problem:** Binance API has rate limits (1200 weight/min)
**Solution:** Use public data for history (95%+), API for recent (5%)

**Result:**
- 365 days of data: ~1 API request (vs ~526)
- 80%+ cost savings
- 10x faster downloads

### Event-Driven Backtesting (Reference)
**Problem:** Vectorized backtesting has look-ahead bias
**Solution:** Process each bar sequentially (realistic)

**Result:**
- No future data leakage
- Realistic execution simulation
- 100% reproducible results

### Reference Architecture
Legacy code provides proven patterns without being actively maintained, keeping the active codebase lean.

---

## 🐛 Troubleshooting

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

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Detailed setup guide
- [docs/ACCEPTANCE_CRITERIA.md](docs/ACCEPTANCE_CRITERIA.md) - Design patterns & reference

---

**Built with lessons learned from 9 months of development on CryptoAnalyzer.**
