# Context for New Claude Code Session

**Last Updated:** 2025-11-14
**Project:** Back-testing-research-tool
**Previous Project:** CryptoAnalyzer (9 months development)

---

## 🎯 Project Mission

Build an **AI-Enhanced Backtesting Research Tool** that combines:
- **Deterministic Core**: Battle-tested Python code for reliable calculations
- **AI Layer**: Natural language interface for strategy exploration and analysis

**Philosophy:** "AI for Intent, Code for Execution"

---

## 📚 Essential Reading (in order)

1. **[README.md](../README.md)** - Architecture, philosophy, quick start
2. **[ACCEPTANCE_CRITERIA.md](./ACCEPTANCE_CRITERIA.md)** - Feature requirements framework
3. **[AI_AGENT_TOOLS_RECOMMENDATIONS.md](./AI_AGENT_TOOLS_RECOMMENDATIONS.md)** - AI tooling options
4. **[MCP_SERVERS_RECOMMENDATIONS.md](./MCP_SERVERS_RECOMMENDATIONS.md)** - MCP integration guide

---

## 🏗️ Current State

### ✅ What We Have (Migrated from Legacy)

**Core Components (Pure Python - 100% Functional):**

1. **Data Layer** (`core/data/`)
   - `BinanceBulkFetcher`: Downloads from data.binance.vision (no API limits)
   - `BinanceDataFetcher`: Binance API for recent data (last ~2 days)
   - `PostgresStorage`: Database storage with deduplication
   - **Key Feature:** Hybrid approach (95%+ data without API limits)

2. **Backtesting Engine** (`core/backtest/`)
   - `BacktestEngine`: Event-driven simulation (deterministic, no look-ahead bias)
   - `Portfolio`: Position tracking, trade history, equity curve
   - `PerformanceMetrics`: Sharpe, max drawdown, win rate, etc.
   - **Key Feature:** 100% reproducible results

3. **Strategies** (`core/backtest/strategies/`)
   - Base strategy class
   - 4 pre-built strategies (MA Crossover, RSI Reversal, MACD, Bollinger)
   - Composition framework (combine multiple signals)
   - Multi-timeframe support

4. **Indicators** (`core/indicators/`)
   - `TechnicalIndicators`: SMA, EMA, RSI, MACD, BB, ATR, VWAP
   - **Key Feature:** Match TA-Lib reference implementations

### ❌ What We DON'T Have Yet

- ❌ AI layer (agents, MCP servers)
- ❌ User interface (CLI or web)
- ❌ Tests (framework exists in `tests/` but empty)
- ❌ Logging/monitoring
- ❌ Error handling/validation (basic only)

---

## 🧠 Critical Context from Legacy Project

### Lessons Learned (9 Months of Development)

#### 1. **Data Fetching: Why Hybrid Approach?**

**Problem We Solved:**
- Binance API has strict rate limits (1200 weight/min)
- Downloading 365 days of hourly data = ~526 API requests
- Rate limits hit frequently, slow downloads

**Solution:**
- Use Binance Public Data (data.binance.vision) for historical (95%+)
- Use API only for recent data (last ~2 days)
- Result: 365 days = ~1 API request (vs 526!)

**Implementation Details:**
- `BinanceBulkFetcher` handles monthly/daily ZIP files
- Automatic timestamp format detection (microseconds for 2025+, milliseconds before)
- Smart strategy: <31 days = daily files, >31 days = monthly + daily

**Cost Savings:**
- 80%+ reduction in API usage
- 10x faster downloads
- No rate limit issues

#### 2. **Backtesting: Why Event-Driven?**

**Problem We Avoided:**
- Vectorized backtesting = look-ahead bias (using future data)
- Unrealistic results (too optimistic)

**Solution:**
- Event-driven: Process each bar sequentially
- Realistic execution: bid/ask spread + slippage + commission
- Deterministic: Same input → same output (always)

**Key Insight:**
- Slower than vectorized BUT accurate
- Performance: >1000 bars/second (good enough for research)

#### 3. **UI Evolution: Streamlit → AI Conversational**

**What We Built (Legacy):**
- Streamlit dashboard with multiple pages
- Chart Generator, Data Management, Backtesting, Strategy Composer
- Worked well but **too much clicking, too rigid**

**What We Want (New):**
- Natural language: "Show me RSI < 30 opportunities last month"
- Conversational workflow: AI guides user through analysis
- Artifacts panel: Charts, tables, metrics (right side)
- Chat panel: Conversation with AI (left side)

**Important:**
- Keep deterministic core (don't let AI execute trades!)
- AI suggests, user confirms, code executes

#### 4. **Configuration Management**

**Current Setup:**
- `.env` file for credentials (Binance API, PostgreSQL)
- `config/config.py` for application settings
- `DataConfig.AVAILABLE_SYMBOLS` for trading pairs

**Key Settings:**
```python
# data.binance.vision cutoff
PUBLIC_DATA_LAG_DAYS = 2  # Data available up to N days ago

# API rate limiting (conservative - 33% margin)
BINANCE_REQUEST_DELAY = 0.15  # seconds between requests
MAX_CANDLES_PER_REQUEST = 1000

# PostgreSQL retention by timeframe
POSTGRES_RETENTION = {
    '1m': 730,   # 2 years
    '1h': 1095,  # 3 years
    '1d': 1825   # 5 years
}
```

#### 5. **Strategy Composition Framework**

**Powerful Feature (Already Implemented):**
- Combine multiple indicators with AND/OR logic
- Multi-timeframe signals (1h + 4h + 1d)
- JSON-based strategy definitions (easy to save/load)

**Example:**
```json
{
  "entry_logic": {
    "operator": "AND",
    "conditions": [
      {"indicator": "RSI", "timeframe": "1h", "operator": "<", "value": 30},
      {"indicator": "SMA", "timeframe": "4h", "operator": "cross_above"}
    ]
  }
}
```

**Use Case for AI:**
- AI generates these JSONs from natural language
- User reviews/edits
- Deterministic code executes

---

## 🔧 Technical Decisions (Important!)

### Database: PostgreSQL

**Why:**
- Proven reliability (9 months production use)
- JSONB support (for strategy metadata)
- Time-series queries are fast
- ON CONFLICT for deduplication

**Schema:**
```sql
candles (
  symbol VARCHAR,
  timeframe VARCHAR,
  open_time TIMESTAMP,
  open DECIMAL,
  high DECIMAL,
  low DECIMAL,
  close DECIMAL,
  volume DECIMAL,
  quote_volume DECIMAL,
  PRIMARY KEY (symbol, timeframe, open_time)
)
```

### Dependencies (requirements.txt)

**Core:**
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `psycopg2-binary>=2.9.6` - PostgreSQL adapter
- `python-binance>=1.0.17` - Binance API client
- `plotly>=5.14.0` - Interactive charts

**Future (AI layer):**
- `anthropic` - Claude API
- `langchain` or `crewai` - Agent framework (TBD)
- Custom MCP servers

### Python Version: 3.12+

**Why:**
- Type hints improvements
- Performance gains
- Modern syntax

---

## 🎨 Proposed Architecture (AI Layer)

### High-Level Design

```
User Natural Language
        ↓
┌───────────────────────────────────┐
│   Supervisor Agent (Claude)       │  ← Understands intent
│   - Parse user request            │
│   - Coordinate workers            │
│   - Format responses              │
└───────┬───────────────────────────┘
        │
        ├─→ Data Worker (Code)         # Fetch data via MCP
        ├─→ Strategy Worker (AI+Code)  # Generate ideas (AI) + validate (code)
        └─→ Backtest Worker (Code)     # Execute backtest (deterministic)
                ↓
        Results → Artifacts Panel
```

### Recommended Approach: **Hybrid Supervisor**

**NOT full AI swarm** (too expensive, unpredictable)
**NOT single agent** (too limited)
**YES supervisor + deterministic workers** (best balance)

**Why:**
- Supervisor (AI): Understanding user intent, coordinating
- Workers (mostly code): Fast, reliable, cheap
- Selective AI: Only for fuzzy tasks (pattern discovery, suggestions)

**Cost Estimate:**
- Full AI: ~$11/hour of usage 💸
- Hybrid: ~$2.20/hour of usage ✅
- 80% cost savings!

### MCP Servers (Model Context Protocol)

**What to Build:**

1. **Binance MCP Server**
   - Operations: fetch_historical, fetch_recent, check_availability
   - Uses: BinanceBulkFetcher + BinanceDataFetcher under the hood
   - Zero AI cost (just wrapper)

2. **PostgreSQL MCP Server**
   - Operations: query_candles, get_symbols, get_timeframes
   - Uses: PostgresStorage
   - Zero AI cost

3. **Strategy MCP Server**
   - Operations: load_strategy, save_strategy, list_strategies
   - File system + JSON
   - Zero AI cost

**Benefit:**
- Standardized interface for AI
- Easy to swap implementations
- Clean separation of concerns

### UI Concept: Dual-Pane Interface

```
┌─────────────────────────────────────────────┐
│  Backtesting Research Tool                  │
├──────────────────┬──────────────────────────┤
│  💬 CHAT         │  📊 ARTIFACTS            │
│  (Left 40%)      │  (Right 60%)             │
│                  │                          │
│  User: "Show me │  ┌────────────────────┐  │
│  BTC RSI < 30"  │  │  Chart: BTC 1h     │  │
│                  │  │  [Plotly]          │  │
│  AI: "Found 12  │  └────────────────────┘  │
│  opportunities. │                          │
│  See chart →"   │  ┌────────────────────┐  │
│                  │  │  Table: Results    │  │
│  User: "Run     │  │  Date | RSI | ...  │  │
│  backtest"      │  └────────────────────┘  │
│                  │                          │
│  AI: "Done. →"  │  ┌────────────────────┐  │
│                  │  │  Metrics           │  │
│                  │  │  Sharpe: 1.8       │  │
│                  │  └────────────────────┘  │
└──────────────────┴──────────────────────────┘
```

**Technology Options:**

**Option 1: Conservative (Recommended for MVP)**
- Streamlit (dual columns: `st.columns([0.4, 0.6])`)
- `st.chat_message` for conversation
- Plotly for charts
- Direct Claude API (no framework overhead)

**Option 2: Modern**
- Gradio (better chat UX)
- Custom React frontend
- LangChain for agents
- More complex but more flexible

**Recommendation:** Start with Option 1, migrate to Option 2 if needed.

---

## 🚨 Critical "Gotchas" to Remember

### 1. **Timestamp Format Change (2025+)**

**IMPORTANT:**
- Binance Public Data changed format on 2025-01-01
- Before: Milliseconds (13 digits): `1609459200000`
- After: Microseconds (16 digits): `1609459200000000`

**Detection Logic (already implemented):**
```python
if timestamp > 1e15:  # 16 digits
    pd.to_datetime(timestamp, unit='us')  # microseconds
else:
    pd.to_datetime(timestamp, unit='ms')  # milliseconds
```

### 2. **PostgreSQL Deduplication**

**Always use:**
```python
INSERT INTO candles (...) VALUES (...)
ON CONFLICT (symbol, timeframe, open_time) DO NOTHING
```

**Why:**
- Prevents duplicate data
- Safe for incremental updates
- Idempotent (can re-run safely)

### 3. **Rate Limiting Strategy**

**Conservative approach:**
```python
BINANCE_REQUEST_DELAY = 0.15  # 150ms between requests
# This gives ~400 requests/minute (well below 1200 weight limit)
# 33% safety margin
```

**Never:**
- Parallel downloads (will hit rate limits)
- Retry without delay (will get banned)
- Ignore weight headers (track usage!)

### 4. **Backtesting Execution**

**Realistic simulation requires:**
```python
commission = 0.001  # 0.1% (Binance default)
slippage = 0.0005   # 0.05% (market orders)

# Execution price != close price
buy_price = close * (1 + slippage)
sell_price = close * (1 - slippage)

# Apply commission to both sides
total_cost = buy_price * (1 + commission)
total_revenue = sell_price * (1 - commission)
```

### 5. **Strategy JSON Validation**

**Before executing strategy:**
- Validate JSON schema
- Check indicator parameters (e.g., RSI period > 0)
- Verify timeframes exist in data
- Validate logic tree (no circular dependencies)

**Don't let AI generate invalid strategies!**

---

## 🎯 Immediate Next Steps (Prioritized)

### Phase 1: Foundation (Week 1)

1. **Setup Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with credentials
   ```

2. **Verify Core Components Work**
   - Test data fetching (hybrid approach)
   - Test backtesting (run simple strategy)
   - Test indicators (calculate RSI, MACD)
   - Write smoke tests

3. **Add Tests** (`tests/`)
   - `test_data_fetcher.py`
   - `test_backtest_engine.py`
   - `test_indicators.py`
   - Target: 80%+ coverage

### Phase 2: AI Integration (Week 2-3)

1. **Build MCP Servers**
   - Start with PostgreSQL MCP (simplest)
   - Then Binance MCP
   - Then Strategy MCP

2. **Prototype Conversational Interface**
   - Streamlit dual-pane UI
   - Direct Claude API (no agents yet)
   - Simple function calling (NLP → Python functions)

3. **Test AI Workflow**
   - "Show me BTC data" → fetch via MCP
   - "Run backtest" → execute deterministic code
   - "Analyze results" → AI interprets metrics

### Phase 3: Advanced Features (Week 4+)

1. **Add Supervisor Agent**
   - Coordinate multiple workers
   - Manage conversation context
   - Handle complex queries

2. **Strategy Generation**
   - AI generates strategy JSONs from NL
   - User reviews/edits
   - Validate before execution

3. **Polish & Optimize**
   - Error handling
   - Logging
   - Performance tuning
   - Cost optimization

---

## 📝 Acceptance Criteria (To Be Defined)

**Framework exists in:** [ACCEPTANCE_CRITERIA.md](./ACCEPTANCE_CRITERIA.md)

**Next step:** Fill in specific criteria for:
- AI natural language understanding (accuracy %)
- Response time (< X seconds)
- Cost per session (< $Y)
- User satisfaction metrics

**Template:**
```markdown
#### AC-XXX: Feature Name
- [ ] Given [context]
- [ ] When [action]
- [ ] Then [outcome]
- [ ] And [constraint]

Success Metrics:
- [Quantifiable measure 1]
- [Quantifiable measure 2]
```

---

## 💡 Design Philosophy Reminders

### ✅ DO:
- Keep critical logic in pure Python (trades, calculations, risk management)
- Use AI for fuzzy tasks (NLP, pattern discovery, suggestions)
- Validate all AI outputs with deterministic code
- Make AI suggestions transparent (user sees reasoning)
- Fail gracefully (fallback to manual if AI fails)

### ❌ DON'T:
- Let AI execute trades directly
- Trust AI calculations without validation
- Use AI for time-critical operations
- Ignore AI costs (monitor usage!)
- Build AI-only features (always have manual fallback)

---

## 🔗 Resources & References

**Legacy Project:**
- https://github.com/Casual159/CryptoAnalyzer (9 months of commits, read for context)

**Binance:**
- Public Data: https://data.binance.vision/
- API Docs: https://binance-docs.github.io/apidocs/
- Rate Limits: [BINANCE_API_LIMITS.md](../BINANCE_API_LIMITS.md) (if exists in legacy)

**AI Frameworks:**
- CrewAI: https://github.com/joaomdmoura/crewAI
- LangChain: https://python.langchain.com/
- MCP: https://modelcontextprotocol.io/

**Testing:**
- pytest: https://docs.pytest.org/
- Coverage: 80%+ target

---

## 🤝 Communication Style

**User Preferences (observed):**
- Prefers Czech language for casual communication
- Likes "vibe coding" (fast prototyping, iterate quickly)
- Values clean architecture over quick hacks
- Appreciates detailed explanations with concrete examples
- Wants to understand trade-offs (cost, performance, complexity)

**Approach:**
- Be methodical (break down complex tasks)
- Provide options with pros/cons
- Ask clarifying questions before major decisions
- Show code examples (not just theory)
- Track progress with todos

---

## 📊 Current Git State

**Repository:** https://github.com/Casual159/Back-testing-research-tool

**Recent Commits:**
```
387215a Docs: Add AI agent and MCP server recommendations
b854b23 Initial commit: Core components migration
```

**Branch:** main
**Working Directory:** `/Users/jakub/Back-testing-research-tool`

**Files Changed (ready to commit):** None (clean state)

---

## 🎬 Suggested Opening Prompt for New Session

```
Hi! I'm continuing work on the Back-testing-research-tool project.

Please read:
1. docs/CONTEXT_FOR_NEW_SESSION.md (this file)
2. README.md
3. docs/ACCEPTANCE_CRITERIA.md

Current focus: [YOUR FOCUS - e.g., "Setup tests" or "Design AI layer" or "Build MCP servers"]

Working directory: /Users/jakub/Back-testing-research-tool

Let me know when you're ready and what you recommend as first steps!
```

---

## ✅ Quick Sanity Checks

**Before starting development:**

1. **Environment:**
   ```bash
   python --version  # Should be 3.12+
   which python      # Should be in venv
   ```

2. **Dependencies:**
   ```bash
   pip list | grep pandas  # Should show 2.0+
   pip list | grep binance # Should show python-binance
   ```

3. **Database:**
   ```bash
   psql -h localhost -U your_user -d trading_bot -c "SELECT version();"
   ```

4. **Core Imports:**
   ```python
   from core.data import BinanceBulkFetcher, PostgresStorage
   from core.backtest import BacktestEngine, Portfolio
   from core.indicators import TechnicalIndicators
   # Should import without errors
   ```

---

**Good luck with the next development session! 🚀**

**Remember:** AI for Intent, Code for Execution.
