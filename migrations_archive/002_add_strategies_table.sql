-- Migration: Add strategies table for strategy management
-- Purpose: Store strategy definitions, descriptions, and metadata
-- Enables AI-driven strategy selection and user strategy library

-- ============================================================================
-- CREATE TABLE: strategies
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategies (
    -- Identity
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    class_name VARCHAR(100) NOT NULL,  -- Python class name (e.g., 'MovingAverageCrossover')

    -- Human description (Markdown format)
    description TEXT NOT NULL,

    -- Structured metadata (JSON format for AI/filtering)
    metadata JSONB NOT NULL DEFAULT '{
        "preferred_regimes": [],
        "avoid_regimes": [],
        "risk_level": "moderate",
        "category": "trend-following",
        "entry_type": "market",
        "exit_type": "market",
        "drawdown_tolerance": "medium",
        "avg_trade_duration": "medium",
        "win_rate_range": [0.4, 0.6]
    }'::jsonb,

    -- Strategy parameters (JSON)
    parameters JSONB NOT NULL,

    -- Optional regime filter (applied during backtest)
    regime_filter JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES for performance
-- ============================================================================

-- Fast lookup by name
CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies(name);

-- Filter by class name (find all MA Crossover variants)
CREATE INDEX IF NOT EXISTS idx_strategies_class ON strategies(class_name);

-- Filter by metadata fields (AI queries)
CREATE INDEX IF NOT EXISTS idx_strategies_metadata ON strategies USING GIN (metadata);

-- Filter by regime preferences
CREATE INDEX IF NOT EXISTS idx_strategies_regime_filter ON strategies USING GIN (regime_filter);

-- ============================================================================
-- COMMENTS for documentation
-- ============================================================================

COMMENT ON TABLE strategies IS
'Strategy definitions for backtesting. Each row represents a configured strategy instance with its parameters and metadata.';

COMMENT ON COLUMN strategies.name IS
'Unique human-readable name for this strategy instance (e.g., "MA Crossover 20/50")';

COMMENT ON COLUMN strategies.class_name IS
'Python class name (e.g., "MovingAverageCrossover"). Used to instantiate strategy.';

COMMENT ON COLUMN strategies.description IS
'Markdown-formatted description explaining strategy intent, regime fit, trade logic, risk profile, and parameters.';

COMMENT ON COLUMN strategies.metadata IS
'Structured metadata for AI filtering and analysis. Includes preferred_regimes, risk_level, category, etc.';

COMMENT ON COLUMN strategies.parameters IS
'Strategy-specific parameters as JSON (e.g., {"fast_period": 20, "slow_period": 50})';

COMMENT ON COLUMN strategies.regime_filter IS
'Optional regime filter. Strategy only trades when market is in these regimes (e.g., ["TREND_UP", "TREND_DOWN"])';

-- ============================================================================
-- TRIGGER: Update updated_at on modification
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- EXAMPLE DATA: Insert MovingAverageCrossover strategy
-- ============================================================================

INSERT INTO strategies (name, class_name, description, metadata, parameters, regime_filter)
VALUES (
    'MA Crossover 20/50',
    'MovingAverageCrossover',

    -- Description (Markdown)
    'Trend-following strategy using two moving averages (fast and slow).

**Best for:** TREND_UP, TREND_DOWN (clear trends)
**Avoid:** RANGE, CHOPPY (whipsaws)

**Entry:** Fast MA crosses above slow MA (golden cross)
**Exit:** Fast MA crosses below slow MA (death cross)

**Risk:** Moderate drawdown during reversals. Requires patience in sideways markets.

**Parameters:**
- `fast_period`: Responsive to recent price (default: 20)
- `slow_period`: Trend baseline (default: 50)',

    -- Metadata (JSONB)
    '{
        "preferred_regimes": ["TREND_UP", "TREND_DOWN"],
        "avoid_regimes": ["RANGE", "CHOPPY"],
        "risk_level": "moderate",
        "category": "trend-following",
        "entry_type": "market",
        "exit_type": "market",
        "drawdown_tolerance": "medium",
        "avg_trade_duration": "medium",
        "win_rate_range": [0.45, 0.55]
    }'::jsonb,

    -- Parameters (JSONB)
    '{
        "fast_period": 20,
        "slow_period": 50
    }'::jsonb,

    -- Regime filter (JSONB array)
    '["TREND_UP", "TREND_DOWN"]'::jsonb
)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Find all trend-following strategies
-- SELECT name, class_name, metadata->>'category' as category
-- FROM strategies
-- WHERE metadata->>'category' = 'trend-following';

-- Find strategies suitable for TREND_UP regime
-- SELECT name, metadata->'preferred_regimes' as regimes
-- FROM strategies
-- WHERE metadata->'preferred_regimes' ? 'TREND_UP';

-- Find low-risk strategies
-- SELECT name, metadata->>'risk_level' as risk
-- FROM strategies
-- WHERE metadata->>'risk_level' = 'low';
