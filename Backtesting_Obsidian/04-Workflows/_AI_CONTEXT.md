# AI Context: Workflows

**Last Updated:** 2024-12-05
**Purpose:** Task routing and workflow guidance for AI sessions
**Read Time:** 2 minutes

---

## 🎯 Quick Task Router

**Use this decision tree to find the right workflow:**

```
What do you need to do?

├─ Add a new technical indicator
│  └─→ [[04-Workflows/FOR_AI_Adding_Indicator]]
│
├─ Create a new API endpoint
│  └─→ [[04-Workflows/FOR_AI_Creating_Endpoint]]
│
├─ Generate documentation from code
│  └─→ [[04-Workflows/FOR_AI_Generating_Docs]]
│
├─ Fetch and store market data
│  └─→ [[04-Workflows/FOR_AI_Fetching_Data]]
│
├─ Set up development environment
│  └─→ [[04-Workflows/Development Setup]]
│
├─ Debug an issue
│  └─→ [[04-Workflows/Troubleshooting]]
│
└─ Something else
   └─→ Check [[02-Components/_AI_CONTEXT]] for component-specific guidance
```

---

## 📋 Available Workflows

### For AI (Step-by-Step Guides)

| Workflow | File | Purpose | Status |
|----------|------|---------|--------|
| **Adding Indicator** | [[04-Workflows/FOR_AI_Adding_Indicator]] | Add new technical indicator | 🚧 To Create |
| **Creating Endpoint** | [[04-Workflows/FOR_AI_Creating_Endpoint]] | Add new FastAPI endpoint | 🚧 To Create |
| **Generating Docs** | [[04-Workflows/FOR_AI_Generating_Docs]] | Auto-generate API/DB docs | 🚧 To Create |
| **Fetching Data** | [[04-Workflows/FOR_AI_Fetching_Data]] | Download and store market data | 🚧 To Create |

### For Humans (Explanatory Guides)

| Workflow | File | Purpose | Status |
|----------|------|---------|--------|
| **Development Setup** | [[04-Workflows/Development Setup]] | Initial project setup | 🚧 To Create |
| **Adding New Indicator** | [[04-Workflows/Adding New Indicator]] | Human-friendly indicator guide | 🚧 To Create |
| **Creating Strategy** | [[04-Workflows/Creating Strategy]] | Strategy composition guide | 🚧 To Create |
| **Troubleshooting** | [[04-Workflows/Troubleshooting]] | Common issues and solutions | 🚧 To Create |

---

## 🤖 Common AI Tasks (Quick Reference)

### Task: "Add a new technical indicator"

**Quick Steps:**
1. Decide: Traditional (vectorized) or Event-Driven (bar-by-bar)?
2. Traditional → Add to `core/indicators/__init__.py`
3. Event-Driven → Create class in `core/indicators/event_driven.py`
4. Follow existing patterns (see RSI, SMA implementations)
5. Add docstrings with examples
6. Update [[02-Components/Indicators]]

**Full Guide:** [[04-Workflows/FOR_AI_Adding_Indicator]]

---

### Task: "Create a new API endpoint"

**Quick Steps:**
1. Open `api/main.py`
2. Add route with decorator: `@app.get("/api/your-endpoint")`
3. Add type hints for auto-validation
4. Call core components (never put logic in endpoint)
5. Return JSON-serializable dict
6. Test with browser or curl
7. Run `python scripts/generate_api_docs.py`

**Full Guide:** [[04-Workflows/FOR_AI_Creating_Endpoint]]

---

### Task: "Generate documentation from code"

**Quick Steps:**
1. For API docs: `python scripts/generate_api_docs.py`
2. For DB schema: `python scripts/generate_db_schema.py`
3. For all docs: `./scripts/generate_all_docs.sh`
4. Commit generated files to `05-Reference/_GENERATED/`

**Full Guide:** [[04-Workflows/FOR_AI_Generating_Docs]]

---

### Task: "Fetch market data for backtesting"

**Quick Steps:**
1. Determine date range (historical vs recent)
2. Use `BinanceBulkFetcher` for >2 days old
3. Use `BinanceDataFetcher` for <2 days old
4. Save with `PostgresStorage.save_candles()` (auto-deduplicates)
5. Verify with `storage.get_candles()`

**Full Guide:** [[04-Workflows/FOR_AI_Fetching_Data]]

---

## 🚨 Critical Workflow Rules

### 1. **Always Read Existing Code First**
Before modifying or adding code:
```
1. Find similar component (e.g., existing indicator)
2. Read its implementation
3. Copy pattern, don't reinvent
4. Maintain consistency
```

### 2. **Never Skip Type Hints**
All Python code MUST have type hints:
```python
# ✅ GOOD
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    ...

# ❌ BAD
def calculate_rsi(df, period=14):
    ...
```

### 3. **Always Update Documentation**
After implementing a feature:
```
1. Update relevant _AI_CONTEXT.md
2. Update/create detailed component doc
3. Run auto-generation scripts if applicable
4. Create session note in 99-Meta/AI_Session_Notes/
```

### 4. **Test Before Claiming Complete**
Don't mark task as done until:
```
1. Code runs without errors
2. Returns expected output
3. Edge cases handled
4. Documentation updated
```

---

## 🔄 Standard Workflow Pattern

**For ALL development tasks, follow this pattern:**

```
1. UNDERSTAND
   ├─ Read relevant _AI_CONTEXT.md
   ├─ Check existing implementations
   └─ Identify files to modify/create

2. PLAN
   ├─ Outline steps
   ├─ Identify potential issues
   └─ Check for dependencies

3. IMPLEMENT
   ├─ Follow existing patterns
   ├─ Add type hints
   ├─ Write docstrings
   └─ Handle edge cases

4. TEST
   ├─ Run the code
   ├─ Verify output
   └─ Test edge cases

5. DOCUMENT
   ├─ Update _AI_CONTEXT.md if needed
   ├─ Update component docs
   ├─ Run auto-generation scripts
   └─ Create session note

6. COMMIT (if requested)
   └─ Follow git workflow
```

---

## 📁 File Organization Guidelines

### Where to put new code:

```
New technical indicator?
  ├─ Traditional → core/indicators/__init__.py
  └─ Event-driven → core/indicators/event_driven.py

New data fetcher?
  └─ core/data/fetchers.py

New database operation?
  └─ core/data/storage.py

New backtesting feature?
  └─ core/backtest/

New API endpoint?
  └─ api/main.py

New React component?
  └─ frontend/components/

New page route?
  └─ frontend/app/[route]/page.tsx

New utility/helper?
  └─ core/utils/ (create if needed)

New script?
  └─ scripts/
```

---

## 🧪 Testing Guidelines

### Manual Testing Checklist:

**For indicators:**
```python
# Test with sample data
import pandas as pd
from core.indicators import TechnicalIndicators

df = pd.DataFrame({
    'close': [100, 102, 101, 103, 105, 104, 106, 108]
})

result = TechnicalIndicators.calculate_sma(df, period=3)
print(result)  # Should show moving average
```

**For API endpoints:**
```bash
# Start server
python api/main.py

# Test endpoint
curl http://localhost:8000/api/your-endpoint

# Or open in browser
open http://localhost:8000/docs  # FastAPI auto-docs
```

**For data fetching:**
```python
from core.data import BinanceBulkFetcher, PostgresStorage

fetcher = BinanceBulkFetcher()
df = fetcher.fetch("BTCUSDT", "1h", days=7)
print(f"Fetched {len(df)} candles")

storage = PostgresStorage()
storage.save_candles(df, "BTCUSDT", "1h")
print("Saved to database")
```

---

## 📊 Auto-Generation Scripts

### Available Scripts:

| Script | Purpose | Output | When to Run |
|--------|---------|--------|------------|
| `generate_api_docs.py` | Extract API endpoints | `api_endpoints.json` | After adding/modifying endpoints |
| `generate_db_schema.py` | Extract DB schema | `database_schema.sql` | After schema changes |
| `generate_types.py` | Generate TypeScript types | `type_definitions.ts` | After Python model changes |
| `generate_all_docs.sh` | Run all generators | All above | Before committing major changes |

**Location:** `scripts/` directory
**Output:** `Backtesting_Obsidian/05-Reference/_GENERATED/`

**Usage:**
```bash
# From project root
python scripts/generate_api_docs.py
python scripts/generate_db_schema.py
python scripts/generate_types.py

# Or all at once
./scripts/generate_all_docs.sh
```

---

## 🔗 Related Documentation

### Component Reference
- **Architecture:** [[01-Architecture/_AI_CONTEXT]]
- **Components:** [[02-Components/_AI_CONTEXT]]
- **Reference:** [[05-Reference/_GENERATED/README]]

### Specific Workflows
- **For AI:** Search `FOR_AI_*.md` in this folder
- **For Humans:** Other `.md` files in this folder

---

## ⚡ Quick Links by Task Type

| Task Type | Start Here |
|-----------|-----------|
| Adding feature | [[02-Components/_AI_CONTEXT]] → Find component → Follow pattern |
| Fixing bug | [[04-Workflows/Troubleshooting]] |
| Setting up project | [[04-Workflows/Development Setup]] |
| Understanding architecture | [[01-Architecture/System Overview]] |
| Finding API reference | [[05-Reference/_GENERATED/README]] |
| Creating documentation | [[04-Workflows/FOR_AI_Generating_Docs]] |

---

**Main Entry:** [[Project Root]]
**Architecture:** [[01-Architecture/_AI_CONTEXT]]
**Components:** [[02-Components/_AI_CONTEXT]]

---

**Last Updated:** 2024-12-05
**Maintained By:** AI + Human collaboration
