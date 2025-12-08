# Auto-Generated Documentation

**Purpose:** This folder contains documentation automatically generated from code  
**DO NOT EDIT MANUALLY** - Changes will be overwritten  
**Last Generated:** Run scripts to update

---

## 📄 Files in This Folder

| File | Generated From | Script | Purpose |
|------|---------------|--------|---------|
| `api_endpoints.json` | FastAPI routes | `scripts/generate_api_docs.py` | API endpoint reference |
| `database_schema.sql` | PostgreSQL | `scripts/generate_db_schema.py` | Database schema dump |
| `type_definitions.ts` | Python types | `scripts/generate_types.py` | TypeScript type definitions |

---

## 🔄 How to Regenerate

### Generate All (Recommended)
```bash
# From project root
./scripts/generate_all_docs.sh
```

### Generate Individual Files
```bash
# API documentation
python scripts/generate_api_docs.py

# Database schema
python scripts/generate_db_schema.py

# TypeScript types
python scripts/generate_types.py
```

---

## ⏱️ When to Regenerate

**Regenerate when:**
- ✅ Added/modified API endpoints in `api/main.py`
- ✅ Changed database schema (migrations, table changes)
- ✅ Modified Python dataclasses or Pydantic models
- ✅ Before committing major changes
- ✅ At the start of each AI session (for fresh context)

**No need to regenerate when:**
- ❌ Only changed business logic (no API/DB changes)
- ❌ Only changed frontend code
- ❌ Only changed documentation

---

## 📊 File Formats

### api_endpoints.json
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Backtesting API",
    "version": "1.0.0"
  },
  "paths": {
    "/api/candlestick/{symbol}/{timeframe}": {
      "get": {
        "summary": "Get Candlestick Data",
        "parameters": [...],
        "responses": {...}
      }
    }
  }
}
```

**Use case:** AI can parse this to understand available endpoints

---

### database_schema.sql
```sql
-- Auto-generated: YYYY-MM-DD HH:MM:SS
-- Database: trading_bot

CREATE TABLE candles (
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMP NOT NULL,
    ...
    PRIMARY KEY (symbol, timeframe, open_time)
);

CREATE INDEX idx_candles_symbol_timeframe ON candles(symbol, timeframe);
```

**Use case:** AI can see exact schema structure, indexes, constraints

---

### type_definitions.ts
```typescript
// Auto-generated from Python types

export interface Candle {
  symbol: string;
  timeframe: string;
  openTime: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
```

**Use case:** Frontend TypeScript code stays in sync with backend

---

## 🚨 Important Notes

### Git Tracking
These files **SHOULD be committed to git** because:
- They serve as documentation
- They provide context for AI
- They show schema evolution over time

But they should be **regenerated frequently** to stay current.

### .gitignore Entry
```gitignore
# Don't ignore _GENERATED files - they're documentation
# DO commit them
```

### Automation (Future)
Consider adding pre-commit hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit
./scripts/generate_all_docs.sh
git add Backtesting_Obsidian/05-Reference/_GENERATED/
```

---

## 🔗 Related Documentation

**For AI:**
- How to use these files: [[_AI_QUICK_START]]
- When to regenerate: [[04-Workflows/FOR_AI_Generating_Docs]]

**For Humans:**
- Human-readable API docs: [[05-Reference/API Endpoints]]
- Human-readable DB docs: [[05-Reference/Database Schema]]

---

## 📝 Generation Scripts

All scripts are located in: `scripts/` directory

**See also:** [[04-Workflows/FOR_AI_Generating_Docs]]

---

**Last Updated:** 2024-12-05  
**Maintained By:** Auto-generation scripts
