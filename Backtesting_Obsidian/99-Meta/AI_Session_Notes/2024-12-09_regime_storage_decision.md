# Dev Session: Market Regime Storage Strategy

**Date:** 2024-12-09
**Session:** Market Regime Classifier - Phase 3A Complete
**Topic:** Storage strategy decision and future AI integration plan

---

## Context

Completing Phase 3A of Market Regime Classifier implementation. API endpoint working, now documenting storage strategy for future AI integration.

---

## Current Status: Compute-On-The-Fly (Option A)

### Implementation
- **Endpoint:** `GET /api/data/regime/{symbol}/{timeframe}`
- **Flow:**
  1. Fetch candles from PostgreSQL
  2. Calculate all technical indicators
  3. Compute regimes event-driven (no lookahead)
  4. Return JSON with regime data + colors

### Performance
- **120 candles:** 0.061s ⚡ (fast enough for MVP)
- **No caching:** Recalculates every request
- **No schema changes:** Uses existing candles table only

### Pros/Cons
✅ **Pros:**
- No database schema changes
- Always uses latest regime detection logic
- No storage overhead
- Simple implementation

❌ **Cons:**
- Repeated computation (inefficient at scale)
- Slower for large datasets (10k+ candles = 2-5s)
- Not suitable for AI agent queries (would recompute every time)

---

## Planned Migration: Pre-computed Storage (Option B)

### When to Implement

**Trigger:** **Before AI integration begins** ⭐

**Rationale:**
- AI research agents will need fast, repeated access to regime data
- Exploratory analysis requires quick iteration
- Complex pattern matching across multiple symbols/timeframes
- Cannot afford 2-5s recomputation per query

### Database Schema

```sql
CREATE TABLE market_regimes (
    -- Primary keys
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMP NOT NULL,

    -- 3D Regime components
    trend_state VARCHAR(20),           -- uptrend | downtrend | neutral
    volatility_state VARCHAR(10),      -- low | high
    momentum_state VARCHAR(20),        -- bullish | bearish | weak

    -- Composite regimes
    full_regime VARCHAR(50),           -- UPTREND_LOWVOL_BULLISH
    simplified_regime VARCHAR(20),     -- TREND_UP | TREND_DOWN | RANGE | CHOPPY | NEUTRAL

    -- Metadata
    confidence FLOAT,                  -- 0.0 - 1.0 confidence score
    created_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (symbol, timeframe, open_time),
    FOREIGN KEY (symbol, timeframe, open_time)
        REFERENCES candles(symbol, timeframe, open_time)
        ON DELETE CASCADE
);

-- Indexes for AI agent queries
CREATE INDEX idx_regime_lookup ON market_regimes(symbol, timeframe, open_time DESC);
CREATE INDEX idx_regime_simplified ON market_regimes(simplified_regime);
CREATE INDEX idx_regime_confidence ON market_regimes(confidence DESC);
```

### Storage Module Extensions

```python
# core/data/storage.py - New methods

class PostgresStorage:
    def insert_regimes(self, df: pd.DataFrame, symbol: str, timeframe: str) -> int:
        """Insert regime data from DataFrame"""

    def get_regimes(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Fetch regime data (with optional date range)"""

    def get_regime_stats(self, symbol: str, timeframe: str) -> dict:
        """Get regime distribution statistics"""

    def delete_regimes(self, symbol: str, timeframe: str) -> int:
        """Delete all regimes for symbol/timeframe"""
```

### Migration Strategy

1. **Backfill Script:** `scripts/backfill_regimes.py`
   - Process all existing symbol/timeframe combinations
   - Calculate indicators + regimes
   - Store in `market_regimes` table

2. **Auto-compute on Fetch:** Modify `BinanceBulkFetcher`
   - After fetching new candles
   - Auto-compute and store regimes
   - Keeps regime data in sync

3. **API Hybrid Approach:**
   - Try pre-computed first (fast path)
   - Fall back to compute-on-fly if not available (backward compatibility)
   - Ensures no breaking changes

---

## Performance Comparison

| Metric | Option A (Current) | Option B (Planned) |
|--------|-------------------|-------------------|
| Small dataset (120 candles) | 0.061s | < 0.010s |
| Large dataset (10k candles) | 2-5s | < 0.050s |
| Repeated queries | Slow (recompute) | Fast (cached) |
| Storage overhead | 0 MB | ~50 KB / 1k candles |
| AI agent friendly | ❌ No | ✅ Yes |

---

## AI Agent Query Examples

**Queries that NEED pre-computed storage:**

```
1. "Show me all TREND_UP periods for BTC 1h in 2024"
   → SQL: SELECT * FROM market_regimes WHERE simplified_regime = 'TREND_UP'
   → Fast: < 50ms

2. "Compare RANGE vs TREND regime performance"
   → Needs to filter backtests by regime
   → Fast regime lookup essential

3. "Find regime transitions: CHOPPY → TREND_UP"
   → Pattern matching across regimes
   → Cannot recompute every time

4. "Regime confidence distribution analysis"
   → Aggregate queries on confidence scores
   → Requires indexed regime data
```

**Without pre-computed storage:**
- Each query recomputes ALL indicators + regimes
- AI waits 2-5s per query
- Not scalable for multi-symbol analysis
- Blocks exploratory workflows

---

## Implementation Checklist (Future)

### Phase A: Schema Preparation
- [ ] Create `market_regimes` table with indexes
- [ ] Add PostgresStorage regime methods
- [ ] Write unit tests for storage operations

### Phase B: Migration
- [ ] Implement backfill script
- [ ] Run backfill on existing data
- [ ] Validate regime data integrity
- [ ] Add auto-compute on data fetch

### Phase C: API Update
- [ ] Update endpoint to use pre-computed (with fallback)
- [ ] Add regime stats endpoint
- [ ] Update frontend (no breaking changes expected)

### Phase D: Monitoring
- [ ] Track regime computation metrics
- [ ] Monitor storage growth (~50 KB / 1k candles)
- [ ] Validate API performance improvements
- [ ] Document migration completion

---

## Decision Summary

**Current (Phase 3A):**
- ✅ Compute-on-the-fly is FINE for MVP
- ✅ 0.061s response time acceptable
- ✅ Frontend development can proceed

**Future (Before AI Integration):**
- ⭐ Migrate to pre-computed storage (Option B)
- ⭐ Essential for AI research agent performance
- ⭐ Non-breaking migration (hybrid approach)
- ⭐ Storage overhead minimal (~50 KB / 1k candles)

**Next Steps:**
- Continue with Phase 3B (Live engine integration) or Phase 4 (Frontend viz)
- Revisit storage migration when AI integration planning begins
- Keep Option B schema documented for easy implementation

---

## Files & References

**Implementation Plan:**
- `/Back-testing-research-tool/.claude/market_regime_implementation_plan.md`
- Section 11: Database Considerations

**Completed:**
- Phase 1: ADX + ROC indicators ✅
- Phase 2: Market Regime Classifier ✅
- Phase 3A: API endpoint (compute-on-fly) ✅

**Pending:**
- Phase 3B: Live engine integration
- Phase 4: Frontend visualization
- Phase 5: Testing & refinement
- Phase X: Pre-computed storage migration (before AI)

**Related Code:**
- `api/main.py:218-279` - Regime endpoint implementation
- `core/indicators/regime.py` - MarketRegimeClassifier
- `core/data/storage.py` - PostgresStorage (needs regime methods)

---

**Session Result:** Storage strategy documented. Proceeding with current implementation (Option A). Migration to Option B documented and ready for AI integration phase.

**Last Updated:** 2024-12-09
