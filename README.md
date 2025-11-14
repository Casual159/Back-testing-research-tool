# Backtesting Research Tool

**AI-Enhanced Cryptocurrency Trading Strategy Research Platform**

Clean slate project built on battle-tested components from [CryptoAnalyzer](https://github.com/Casual159/CryptoAnalyzer).

---

## 🎯 Philosophy

### Core Principle: **AI for Intent, Code for Execution**

- **AI Layer**: Understands user intent, suggests strategies, analyzes results
- **Code Layer**: Deterministic backtesting, precise calculations, reliable data

### What This Means:

✅ **AI will help you:**
- Formulate strategy ideas from natural language
- Discover patterns in market data
- Interpret backtest results
- Suggest optimizations

❌ **AI will NOT:**
- Execute trades (pure Python code)
- Calculate metrics (deterministic math)
- Manage portfolio (exact accounting)
- Fetch data (reliable API calls)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              AI Layer (Future)                  │
│  Natural language → Strategy parameters         │
│  "Find RSI < 30 opportunities"                  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│           Core Components (Pure Code)           │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  Data Layer  │  │  Backtesting │            │
│  │  (Hybrid)    │  │    Engine    │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐                               │
│  │  Indicators  │  (Deterministic, Fast)        │
│  └──────────────┘                               │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│               Data Storage                      │
│  PostgreSQL + Binance Public Data + API         │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL
- Binance API keys (optional for recent data)

### Installation

```bash
# Clone repository
git clone https://github.com/Casual159/Back-testing-research-tool.git
cd Back-testing-research-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Database Setup

```bash
# macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb trading_bot

# Test connection
python -c "from core.data import PostgresStorage; print('✅ Database connected!')"
```

---

## 📦 Core Components

### Data Layer

**Hybrid approach** for optimal cost/speed:

- **Binance Public Data** (data.binance.vision)
  - Historical data from inception to ~2 days ago
  - No API limits, fast downloads
  - Monthly/daily ZIP files

- **Binance API** (fallback)
  - Recent data (last ~2 days)
  - Minimal API usage

```python
from core.data import BinanceBulkFetcher, PostgresStorage

# Fetch historical data (automatic hybrid approach)
fetcher = BinanceBulkFetcher()
data = fetcher.fetch_historical('BTCUSDT', '1h', start_date, end_date)

# Store to PostgreSQL
storage = PostgresStorage(config)
storage.insert_candles(data, 'BTCUSDT', '1h')
```

**See:** [Acceptance Criteria - Data Layer](docs/ACCEPTANCE_CRITERIA.md#data-layer)

### Backtesting Engine

Event-driven, deterministic backtesting:

```python
from core.backtest import BacktestEngine, Portfolio
from core.backtest.strategies import RSIReversalStrategy

# Setup
portfolio = Portfolio(initial_capital=10000)
strategy = RSIReversalStrategy(rsi_period=14, oversold=30, overbought=70)

# Run backtest
engine = BacktestEngine(portfolio, strategy)
results = engine.run(data)

# Analyze
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
```

**See:** [Acceptance Criteria - Backtesting](docs/ACCEPTANCE_CRITERIA.md#backtesting-engine)

### Technical Indicators

Battle-tested implementations:

```python
from core.indicators import TechnicalIndicators

# Calculate indicators
rsi = TechnicalIndicators.rsi(close_prices, period=14)
macd, signal, hist = TechnicalIndicators.macd(close_prices)
bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(close_prices)
```

**Supported:**
- SMA, EMA, RSI, MACD, Bollinger Bands, ATR, VWAP

**See:** [Acceptance Criteria - Indicators](docs/ACCEPTANCE_CRITERIA.md#technical-indicators)

---

## 📚 Documentation

- **[Acceptance Criteria](docs/ACCEPTANCE_CRITERIA.md)** - Feature requirements & success metrics
- **[Legacy Project](https://github.com/Casual159/CryptoAnalyzer)** - Original implementation & learnings

---

## 🛠️ Development

### Project Structure

```
Back-testing-research-tool/
├── core/                    # Core deterministic components
│   ├── data/               # Data fetching & storage
│   │   ├── bulk_fetcher.py # Binance Public Data
│   │   ├── fetcher.py      # Binance API
│   │   └── storage.py      # PostgreSQL
│   ├── backtest/           # Backtesting engine
│   │   ├── engine.py       # Event-driven simulator
│   │   ├── portfolio.py    # Position tracking
│   │   ├── metrics.py      # Performance metrics
│   │   └── strategies/     # Strategy implementations
│   └── indicators/         # Technical indicators
│       └── technical.py
├── config/                 # Configuration
│   └── config.py
├── docs/                   # Documentation
│   └── ACCEPTANCE_CRITERIA.md
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=core --cov-report=html
```

### Code Quality

```bash
# Format code
black core/ tests/

# Lint
flake8 core/ tests/

# Type check
mypy core/
```

---

## 🎯 Roadmap

### Phase 1: Core Foundation (Current)
- ✅ Data layer (hybrid fetcher)
- ✅ Backtesting engine
- ✅ Technical indicators
- ✅ Acceptance criteria framework

### Phase 2: AI Integration (Next)
- [ ] MCP servers (Binance, PostgreSQL, Strategy)
- [ ] AI agent for strategy suggestion
- [ ] Natural language interface
- [ ] Conversational backtest workflow

### Phase 3: Advanced Features
- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization
- [ ] Risk management
- [ ] Live trading integration

---

## 💡 Design Decisions

### Why Hybrid Data Fetcher?

**Problem:** Binance API has rate limits (1200 weight/min)
**Solution:** Use public data for history (95%+), API for recent (5%)

**Result:**
- 365 days of data: ~1 API request (vs ~526)
- 80%+ cost savings
- 10x faster downloads

### Why Event-Driven Backtesting?

**Problem:** Vectorized backtesting has look-ahead bias
**Solution:** Process each bar sequentially (realistic)

**Result:**
- No future data leakage
- Realistic execution simulation
- 100% reproducible results

### Why Deterministic Core?

**Problem:** AI is unpredictable (hallucinations, drift)
**Solution:** Keep critical logic in pure Python code

**Result:**
- Reliable calculations
- Fast performance
- Easy debugging
- Low cost

---

## 🤝 Contributing

This is a personal research project, but ideas and feedback are welcome!

---

## 📄 License

MIT License - See LICENSE file

---

## 🔗 Links

- **Legacy Project:** [CryptoAnalyzer](https://github.com/Casual159/CryptoAnalyzer)
- **Binance Public Data:** https://data.binance.vision/
- **Binance API Docs:** https://binance-docs.github.io/apidocs/

---

**Built with lessons learned from 9 months of development on CryptoAnalyzer.**

**Clean slate. Battle-tested core. AI-enhanced when it matters.**
