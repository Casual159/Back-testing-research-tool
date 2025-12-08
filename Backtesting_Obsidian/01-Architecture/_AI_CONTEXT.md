# AI Context: Architecture

**Last Updated:** 2024-12-05  
**Purpose:** Quick architectural reference for AI sessions  
**Read Time:** 2 minutes

---

## 🎯 What AI Needs to Know

### System Architecture Overview

The system follows a **three-tier architecture**:

```
┌─────────────────────────────────────────────┐
│           Frontend (Next.js)                │
│  - React components                         │
│  - Chart visualization (Plotly)             │
│  - Dynamic routing                          │
└─────────────┬───────────────────────────────┘
              │ HTTP/JSON
┌─────────────▼───────────────────────────────┐
│           Backend (FastAPI)                 │
│  - REST API endpoints                       │
│  - Request validation                       │
│  - Business logic coordination              │
└─────────────┬───────────────────────────────┘
              │ Python calls
┌─────────────▼───────────────────────────────┐
│        Core Python (Deterministic)          │
│  - Data fetching (BinanceBulk + API)        │
│  - Database storage (PostgreSQL)            │
│  - Backtesting engine (event-driven)        │
│  - Technical indicators                     │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│         PostgreSQL Database                 │
│  - Candle data (OHLCV)                      │
│  - Strategy definitions (future)            │
│  - Backtest results (future)                │
└─────────────────────────────────────────────┘
```

---

## 🧭 Quick Decision Tree for AI

### "Where does this logic belong?"

```
Is it about UI/UX presentation?
  └─→ Frontend (Next.js components)

Is it about HTTP API routing?
  └─→ Backend (FastAPI endpoints in api/main.py)

Is it about data/calculations/trading logic?
  └─→ Core Python (core/ directory)
      ├─ Data operations? → core/data/
      ├─ Backtesting? → core/backtest/
      ├─ Indicators? → core/indicators/
      └─ Models/Types? → core/models/ (future)
```

### "Which data fetching method should I use?"

```
Need historical data (>2 days old)?
  └─→ BinanceBulkFetcher
      - Uses data.binance.vision (no API limits)
      - Downloads monthly/daily ZIP files
      - Fast and free
      - File: core/data/fetchers.py:15-145

Need recent data (<2 days old)?
  └─→ BinanceDataFetcher
      - Uses Binance REST API
      - Rate limited (1200 weight/min)
      - Real-time data
      - File: core/data/fetchers.py:147-230

Need to store data?
  └─→ PostgresStorage
      - Always use ON CONFLICT DO NOTHING
      - Automatic deduplication
      - File: core/data/storage.py:10-95
```

---

## 🚨 Critical Architectural Rules

### 1. **Separation of Concerns**
- **Frontend:** Presentation only, no business logic
- **Backend (FastAPI):** Routing and validation, minimal logic
- **Core Python:** ALL business logic, calculations, trading decisions

**Why:** Core can be tested independently, reused in different contexts, and AI can't accidentally break critical logic through UI changes.

### 2. **Deterministic Core Principle**
- Core Python MUST be deterministic (same input → same output, always)
- NO randomness in core logic
- NO AI decision-making in core logic
- NO network calls in calculation functions

**Why:** Trading strategies must be reproducible for backtesting validation.

### 3. **Database Deduplication**
Every insert MUST use:
```python
INSERT INTO candles (...) VALUES (...)
ON CONFLICT (symbol, timeframe, open_time) DO NOTHING
```

**Why:** Prevents duplicate data, enables safe re-runs, idempotent operations.

### 4. **Hybrid Data Fetching Strategy**
- Use BulkFetcher for 95%+ of historical data (free, fast)
- Use API only for recent data (expensive, rate-limited)
- NEVER download historical data via API if avoidable

**Why:** Cost savings (80%+ reduction in API usage), speed (10x faster), no rate limits.

---

## 📊 Technology Stack

| Layer | Technology | Version | Why Chosen |
|-------|-----------|---------|------------|
| **Frontend** | Next.js | 15.x | React framework, SSR, routing |
| | React | 19.x | UI components |
| | TypeScript | 5.x | Type safety |
| | Plotly.js | Latest | Financial charts |
| **Backend** | FastAPI | Latest | Fast, auto-docs, async |
| | Python | 3.12+ | Modern syntax, performance |
| | Uvicorn | Latest | ASGI server |
| **Core** | Pandas | 2.0+ | Data manipulation |
| | NumPy | 1.24+ | Numerical computing |
| | psycopg2 | 2.9+ | PostgreSQL adapter |
| | python-binance | 1.0+ | Binance API client |
| **Database** | PostgreSQL | 14+ | Reliability, JSONB, time-series |
| **Future AI** | Anthropic Claude | Latest | Natural language interface |
| | MCP Servers | - | Model Context Protocol |

**Full details:** [[01-Architecture/Tech Stack]]

---

## 🔄 Data Flow Example

### Example: "User requests BTC candlestick chart for last 30 days"

```
1. User opens frontend page
   └─→ GET /chart/BTCUSDT/1h

2. Next.js page component loads
   └─→ Calls API: GET /api/candlestick/BTCUSDT/1h?limit=720

3. FastAPI endpoint receives request
   └─→ api/main.py:get_candlestick_data()
   └─→ Validates parameters (symbol, timeframe, limit)

4. Backend calls Core Python
   └─→ storage = PostgresStorage()
   └─→ data = storage.get_candles("BTCUSDT", "1h", limit=720)

5. Core queries PostgreSQL
   └─→ SELECT * FROM candles 
       WHERE symbol='BTCUSDT' AND timeframe='1h'
       ORDER BY open_time DESC LIMIT 720

6. If data incomplete, fetch missing data
   └─→ fetcher = BinanceBulkFetcher()  # For old data
   └─→ fetcher = BinanceDataFetcher()  # For recent data
   └─→ storage.save_candles(new_data)

7. Return data to FastAPI
   └─→ Format as JSON with color logic

8. FastAPI returns to frontend
   └─→ JSON response with OHLCV data

9. React component renders chart
   └─→ Plotly.js candlestick chart
   └─→ User sees interactive chart
```

**Detailed flow:** [[01-Architecture/Data Flow]]

---

## 🏗️ Design Patterns Used

### 1. **Repository Pattern**
- `PostgresStorage` abstracts database operations
- Core logic doesn't know about SQL
- Easy to swap database implementations

### 2. **Strategy Pattern**
- Backtesting strategies follow base class
- Composable strategy logic
- File: `core/backtest/strategies/base.py`

### 3. **Factory Pattern** (Future)
- Indicator factory for dynamic indicator creation
- Strategy factory for JSON → Strategy object

### 4. **Facade Pattern**
- FastAPI endpoints are facades over core logic
- Simple API surface, complex logic hidden

---

## 📍 Where to Find Details

### Architecture Documentation
- **System Overview:** [[01-Architecture/System Overview]]
- **Data Flow:** [[01-Architecture/Data Flow]]
- **Tech Stack Rationale:** [[01-Architecture/Tech Stack]]
- **Design Decisions (ADRs):** [[01-Architecture/Design Decisions]]

### Related Contexts
- **Component Details:** [[02-Components/_AI_CONTEXT]]
- **Workflow Guides:** [[04-Workflows/_AI_CONTEXT]]
- **API Reference:** [[05-Reference/_GENERATED/api_endpoints.json]]
- **Database Schema:** [[05-Reference/_GENERATED/database_schema.sql]]

---

## 🔗 Key Files to Know

| File | Purpose | AI Can Modify? |
|------|---------|----------------|
| `api/main.py` | FastAPI endpoints | ✅ YES (with caution) |
| `core/data/fetchers.py` | Data fetching logic | ⚠️ REVIEW REQUIRED |
| `core/data/storage.py` | Database operations | ❌ APPROVAL NEEDED |
| `core/backtest/engine.py` | Backtesting engine | ❌ APPROVAL NEEDED |
| `core/indicators/__init__.py` | Technical indicators | ✅ YES (for new indicators) |
| `frontend/components/*.tsx` | React components | ✅ YES |
| `frontend/app/**/*.tsx` | Next.js pages | ✅ YES |

---

## 🧠 Mental Model for AI

**Think of the system as:**

```
Frontend = Presentation Layer (what user sees)
    ↓
Backend = Traffic Controller (routes requests)
    ↓
Core = Brain (all the smart logic)
    ↓
Database = Memory (persistent storage)
```

**When adding a feature, ask:**
1. What does the user see? → Frontend component
2. What HTTP endpoint do they call? → Backend route
3. What logic executes? → Core function
4. What data is needed? → Database query

---

## ⚡ Quick Reference Links

**Main Entry:** [[Project Root]]  
**Component Deep Dives:** [[02-Components/_AI_CONTEXT]]  
**Common Tasks:** [[04-Workflows/_AI_CONTEXT]]  
**Auto-Generated Schemas:** [[05-Reference/_GENERATED/README]]

---

**Last Updated:** 2024-12-05  
**Maintained By:** AI + Human collaboration
