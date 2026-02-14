# AI Context: Components Overview

**Last Updated:** 2024-12-05
**Purpose:** Quick component lookup for AI sessions
**Read Time:** 3 minutes

---

## 🎯 Component Status Matrix

| Component | File Location | Status | AI Can Modify? | Last Updated |
|-----------|--------------|--------|----------------|--------------|
| **BinanceBulkFetcher** | `core/data/fetchers.py:15-145` | ✅ Stable | ⚠️ Review needed | 2024-11-14 |
| **BinanceDataFetcher** | `core/data/fetchers.py:147-230` | ✅ Stable | ⚠️ Review needed | 2024-11-14 |
| **PostgresStorage** | `core/data/storage.py:10-95` | ✅ Stable | ❌ Approval needed | 2024-11-14 |
| **BacktestEngine** | `core/backtest/engine.py` | ✅ Stable | ❌ Approval needed | 2024-11-14 |
| **Portfolio** | `core/backtest/portfolio.py` | ✅ Stable | ❌ Approval needed | 2024-11-14 |
| **TechnicalIndicators** | `core/indicators/__init__.py` | 🚧 In Progress | ✅ YES (new only) | 2024-12-03 |
| **EventDrivenIndicators** | `core/indicators/event_driven.py` | 🚧 In Progress | ✅ YES | 2024-12-05 |
| **FastAPI Endpoints** | `api/main.py` | ✅ Stable | ✅ YES | 2024-12-03 |
| **CandlestickChart** | `frontend/components/CandlestickChart.tsx` | ✅ Stable | ✅ YES | 2024-12-03 |
| **Chart Page** | `frontend/app/chart/[symbol]/[timeframe]/page.tsx` | ✅ Stable | ✅ YES | 2024-12-03 |
| **AIAgent** | `core/ai/` | ❌ Not Started | - | - |
| **MCP Servers** | `mcp/` | ❌ Not Started | - | - |

**Legend:**
- ✅ **Stable** - Production ready, tested
- 🚧 **In Progress** - Partially implemented
- ❌ **Not Started** - Planned but not implemented
- ✅ **YES** - AI can freely modify
- ⚠️ **Review needed** - AI can modify but human should review
- ❌ **Approval needed** - AI must ask before modifying

---

## 🧭 Quick Decision Tree for Components

### "I need to fetch data..."

```
What kind of data?

├─ Historical candle data (>2 days old)
│  └─→ Use: BinanceBulkFetcher
│     - Method: fetch(symbol, timeframe, days)
│     - Returns: pandas.DataFrame
│     - File: core/data/fetchers.py:15-145
│     - Example: fetcher.fetch("BTCUSDT", "1h", days=30)
│
├─ Recent candle data (<2 days old)
│  └─→ Use: BinanceDataFetcher
│     - Method: fetch_recent(symbol, timeframe, limit)
│     - Returns: pandas.DataFrame
│     - File: core/data/fetchers.py:147-230
│     - Example: fetcher.fetch_recent("BTCUSDT", "1h", limit=100)
│
└─ Data from database
   └─→ Use: PostgresStorage
      - Method: get_candles(symbol, timeframe, limit, start, end)
      - Returns: pandas.DataFrame
      - File: core/data/storage.py:10-95
      - Example: storage.get_candles("BTCUSDT", "1h", limit=1000)
```

### "I need to calculate indicators..."

```
What type of indicator?

├─ Traditional (vectorized, full dataset)
│  └─→ Use: TechnicalIndicators
│     - Methods: calculate_sma(), calculate_rsi(), etc.
│     - Input: pandas.DataFrame with OHLCV
│     - Output: pandas.Series or DataFrame with indicator values
│     - File: core/indicators/__init__.py
│     - Example: TechnicalIndicators.calculate_rsi(df, period=14)
│
└─ Event-driven (bar-by-bar, for backtesting)
   └─→ Use: EventDrivenIndicators (NEW!)
      - Methods: update(), get_value()
      - Input: Single candle at a time
      - Output: Current indicator value
      - File: core/indicators/event_driven.py
      - Example: indicator.update(candle); value = indicator.get_value()
```

### "I need to run a backtest..."

```
└─→ Use: BacktestEngine
   - Method: run(strategy, data, initial_capital)
   - Input: Strategy object, DataFrame, float
   - Output: BacktestResults object
   - File: core/backtest/engine.py
   - Example:
     engine = BacktestEngine()
     results = engine.run(
         strategy=MyStrategy(),
         data=candles_df,
         initial_capital=10000.0
     )
```

### "I need to create an API endpoint..."

```
└─→ Add to: api/main.py
   - Use FastAPI decorators: @app.get(), @app.post()
   - Add type hints for auto-validation
   - Return JSON-serializable objects
   - Example:
     @app.get("/api/indicators/{symbol}/{timeframe}")
     async def get_indicators(
         symbol: str,
         timeframe: str,
         indicator: str = "RSI"
     ) -> dict:
         # Implementation
         return {"data": [...]}
```

### "I need to create a UI component..."

```
├─ Chart/visualization
│  └─→ Create in: frontend/components/
│     - Use React + TypeScript
│     - Import Plotly for charts
│     - Example: CandlestickChart.tsx
│
└─ Page/route
   └─→ Create in: frontend/app/
      - Use Next.js App Router
      - Dynamic routes: [param]/page.tsx
      - Example: app/chart/[symbol]/[timeframe]/page.tsx
```

---

## 📚 Component Details

### 1. Data Layer Components

#### BinanceBulkFetcher
**Purpose:** Download historical data from data.binance.vision (no API limits)

**Key Methods:**
```python
def fetch(
    symbol: str,          # e.g., "BTCUSDT"
    timeframe: str,       # e.g., "1h", "1d"
    days: int = 30,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame
```

**Returns:** DataFrame with columns: `open_time, open, high, low, close, volume, quote_volume`

**When to use:** Historical data older than 2 days

**Gotchas:**
- Timestamp format changed in 2025 (ms → μs)
- Uses monthly files for >31 days, daily files for ≤31 days
- Public data has 2-day lag

**Details:** [[02-Components/Data Layer#BinanceBulkFetcher]]

---

#### BinanceDataFetcher
**Purpose:** Fetch recent data via Binance REST API

**Key Methods:**
```python
def fetch_recent(
    symbol: str,
    timeframe: str,
    limit: int = 100      # Max 1000
) -> pd.DataFrame
```

**When to use:** Data from last 2 days

**Gotchas:**
- Rate limited (1200 weight/min)
- Max 1000 candles per request
- Has 150ms delay between requests

**Details:** [[02-Components/Data Layer#BinanceDataFetcher]]

---

#### PostgresStorage
**Purpose:** Save and retrieve candle data from PostgreSQL

**Key Methods:**
```python
def save_candles(df: pd.DataFrame, symbol: str, timeframe: str) -> None
def get_candles(
    symbol: str,
    timeframe: str,
    limit: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> pd.DataFrame
```

**Critical:** Always uses `ON CONFLICT DO NOTHING` for deduplication

**Details:** [[02-Components/Data Layer#PostgresStorage]]

---

### 2. Backtesting Components

#### BacktestEngine
**Purpose:** Event-driven backtesting simulation

**Key Characteristics:**
- Processes candles sequentially (no look-ahead bias)
- Simulates realistic execution (slippage + commission)
- Deterministic (same input → same output)

**DO NOT MODIFY** without explicit approval - critical trading logic

**Details:** [[02-Components/Backtesting Engine]]

---

#### Portfolio
**Purpose:** Track positions, trades, and equity during backtest

**Key Methods:**
```python
def open_position(symbol, side, size, price)
def close_position(symbol, price)
def get_equity()
def get_trades()
```

**DO NOT MODIFY** without approval - handles money calculations

**Details:** [[02-Components/Backtesting Engine#Portfolio]]

---

### 3. Indicator Components

#### TechnicalIndicators (Traditional)
**Purpose:** Calculate technical indicators on complete datasets

**Available Indicators:**
- `calculate_sma(df, period)` - Simple Moving Average
- `calculate_ema(df, period)` - Exponential Moving Average
- `calculate_rsi(df, period)` - Relative Strength Index
- `calculate_macd(df, fast, slow, signal)` - MACD
- `calculate_bollinger_bands(df, period, std)` - Bollinger Bands
- `calculate_atr(df, period)` - Average True Range
- `calculate_vwap(df)` - Volume Weighted Average Price

**AI CAN ADD NEW INDICATORS** - follow existing pattern

**Details:** [[02-Components/Indicators#Traditional]]

---

#### EventDrivenIndicators (NEW - In Progress)
**Purpose:** Calculate indicators bar-by-bar for backtesting

**Pattern:**
```python
class RSIIndicator:
    def __init__(self, period: int = 14):
        self.period = period
        self.history = []

    def update(self, candle: dict) -> None:
        """Update with new candle"""
        self.history.append(candle['close'])
        # Calculate RSI

    def get_value(self) -> Optional[float]:
        """Get current RSI value"""
        if len(self.history) < self.period:
            return None
        return self._calculate_rsi()
```

**AI CAN IMPLEMENT NEW EVENT-DRIVEN INDICATORS**

**Details:** [[02-Components/Indicators#Event-Driven]]

---

### 4. API Components

#### FastAPI Endpoints (api/main.py)
**Purpose:** HTTP API for frontend

**Current Endpoints:**
- `GET /api/candlestick/{symbol}/{timeframe}` - Get candle data
  - Parameters: `limit` (default 100)
  - Returns: JSON with OHLCV + colors

**AI CAN ADD NEW ENDPOINTS** - follow FastAPI patterns

**Details:** [[02-Components/API Layer]]

---

### 5. Frontend Components

#### CandlestickChart.tsx
**Purpose:** Interactive candlestick chart with Plotly

**Props:**
```typescript
interface CandlestickChartProps {
  data: CandleData[];
  symbol: string;
  timeframe: string;
}
```

**AI CAN MODIFY** and create new chart components

**Details:** [[02-Components/Frontend#Chart Components]]

---

#### Chart Page (app/chart/[symbol]/[timeframe]/page.tsx)
**Purpose:** Dynamic route for chart viewing

**AI CAN CREATE NEW PAGES** following Next.js App Router patterns

**Details:** [[02-Components/Frontend#Pages]]

---

## 🚨 Critical Component Rules

### 1. **Data Deduplication**
When using `PostgresStorage.save_candles()`, it automatically handles deduplication via:
```sql
ON CONFLICT (symbol, timeframe, open_time) DO NOTHING
```
**Never disable this!** It prevents data corruption.

### 2. **Event-Driven Backtesting**
When implementing indicators for backtesting:
- ✅ **DO:** Use event-driven pattern (update bar-by-bar)
- ❌ **DON'T:** Use vectorized calculations (look-ahead bias)

### 3. **Timestamp Format Detection**
BinanceBulkFetcher auto-detects timestamp format:
```python
if timestamp > 1e15:  # 16 digits
    pd.to_datetime(timestamp, unit='us')  # microseconds (2025+)
else:
    pd.to_datetime(timestamp, unit='ms')  # milliseconds (pre-2025)
```
**Never hardcode timestamp parsing!**

### 4. **Rate Limiting**
BinanceDataFetcher has built-in rate limiting:
```python
BINANCE_REQUEST_DELAY = 0.15  # 150ms between requests
```
**Never remove or reduce this!** Will get banned.

---

## 📊 Component Dependencies

```
Frontend Components
    ↓ (HTTP requests)
FastAPI Endpoints
    ↓ (Python calls)
Core Components (Data, Backtest, Indicators)
    ↓ (SQL queries)
PostgreSQL Database
```

**Rule:** Higher layers can call lower layers, but NEVER the reverse.

---

## 🔧 Adding New Components

### Checklist for New Component:
1. ✅ Decide which layer (Data/Backtest/Indicator/API/Frontend)
2. ✅ Create file in appropriate `core/` subfolder
3. ✅ Follow existing patterns (see similar components)
4. ✅ Add type hints (Python) or types (TypeScript)
5. ✅ Write docstrings explaining purpose
6. ✅ Update this `_AI_CONTEXT.md` with new component
7. ✅ Create detailed doc in [[02-Components/]]
8. ✅ Add to [[05-Reference/_GENERATED/]] if applicable
9. ✅ Link from [[Project Root]]

---

## 📍 Where to Find Details

### Component Deep Dives
- **Data Layer:** [[02-Components/Data Layer]]
- **Backtesting Engine:** [[02-Components/Backtesting Engine]]
- **Indicators:** [[02-Components/Indicators]]
- **API Layer:** [[02-Components/API Layer]]
- **Frontend:** [[02-Components/Frontend]]

### Related Contexts
- **Architecture:** [[01-Architecture/_AI_CONTEXT]]
- **Workflows:** [[04-Workflows/_AI_CONTEXT]]
- **Auto-Generated Schemas:** [[05-Reference/_GENERATED/README]]

---

## ⚡ Quick Component Lookup

| I Want To... | Use This Component |
|-------------|-------------------|
| Download historical data | [[02-Components/Data Layer#BinanceBulkFetcher]] |
| Fetch recent data | [[02-Components/Data Layer#BinanceDataFetcher]] |
| Save data to database | [[02-Components/Data Layer#PostgresStorage]] |
| Query data from database | [[02-Components/Data Layer#PostgresStorage]] |
| Calculate RSI on full dataset | [[02-Components/Indicators#Traditional]] |
| Calculate RSI bar-by-bar | [[02-Components/Indicators#Event-Driven]] |
| Run a backtest | [[02-Components/Backtesting Engine]] |
| Create API endpoint | [[02-Components/API Layer]] |
| Create chart component | [[02-Components/Frontend#Charts]] |
| Create new page | [[02-Components/Frontend#Pages]] |

---

**Main Entry:** [[Project Root]]
**Architecture Context:** [[01-Architecture/_AI_CONTEXT]]
**Task Workflows:** [[04-Workflows/_AI_CONTEXT]]

---

**Last Updated:** 2024-12-05
**Maintained By:** AI + Human collaboration
