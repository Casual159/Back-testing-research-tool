-- Migration: Add market_regimes table for pre-computed regime data
-- Purpose: Store regime classifications for AI-driven analysis and fast API queries
-- Performance: ~6x faster queries (10ms vs 61ms compute-on-fly)
-- Storage: ~50 KB per 1000 candles

-- ============================================================================
-- CREATE TABLE: market_regimes
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_regimes (
    -- Primary keys (same as candles table)
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMP NOT NULL,

    -- 3D Regime components (raw classification values)
    trend_state VARCHAR(20),            -- 'uptrend' | 'downtrend' | 'neutral'
    volatility_state VARCHAR(10),       -- 'low' | 'high'
    momentum_state VARCHAR(20),         -- 'bullish' | 'bearish' | 'weak'

    -- Composite regimes (derived values)
    full_regime VARCHAR(50),            -- 'UPTREND_LOWVOL_BULLISH'
    simplified_regime VARCHAR(20),      -- 'TREND_UP' | 'TREND_DOWN' | 'RANGE' | 'CHOPPY' | 'NEUTRAL'

    -- Metadata
    confidence FLOAT,                   -- 0.0 - 1.0 (classification confidence)
    classifier_version VARCHAR(10) DEFAULT 'v1.0',  -- Track algorithm version
    created_at TIMESTAMP DEFAULT NOW(), -- Record creation timestamp

    -- Constraints
    PRIMARY KEY (symbol, timeframe, open_time),
    FOREIGN KEY (symbol, timeframe, open_time)
        REFERENCES candles(symbol, timeframe, open_time)
        ON DELETE CASCADE,

    -- Validation constraints
    CONSTRAINT valid_trend CHECK (trend_state IN ('uptrend', 'downtrend', 'neutral')),
    CONSTRAINT valid_volatility CHECK (volatility_state IN ('low', 'high')),
    CONSTRAINT valid_momentum CHECK (momentum_state IN ('bullish', 'bearish', 'weak')),
    CONSTRAINT valid_simplified CHECK (simplified_regime IN ('TREND_UP', 'TREND_DOWN', 'RANGE', 'CHOPPY', 'NEUTRAL')),
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

-- ============================================================================
-- INDEXES for performance
-- ============================================================================

-- Primary time-series index (most common query pattern)
CREATE INDEX idx_regime_time_range
ON market_regimes(symbol, timeframe, open_time DESC);

-- Simplified regime filtering (AI agent queries)
CREATE INDEX idx_regime_simplified
ON market_regimes(simplified_regime, open_time DESC);

-- Confidence-based filtering (high-quality detections)
CREATE INDEX idx_regime_confidence
ON market_regimes(confidence DESC)
WHERE confidence > 0.7;

-- Partial index for high-confidence simplified regimes (fast AI queries)
CREATE INDEX idx_regime_high_quality
ON market_regimes(simplified_regime, symbol, timeframe, open_time DESC)
WHERE confidence > 0.7;

-- Composite index for full regime analysis
CREATE INDEX idx_regime_components
ON market_regimes(trend_state, volatility_state, momentum_state);

-- ============================================================================
-- COMMENTS for documentation
-- ============================================================================

COMMENT ON TABLE market_regimes IS
'Pre-computed market regime classifications for fast querying and AI analysis. Each row corresponds to one candle with its regime state.';

COMMENT ON COLUMN market_regimes.trend_state IS
'Trend direction: uptrend (bullish), downtrend (bearish), or neutral (sideways)';

COMMENT ON COLUMN market_regimes.volatility_state IS
'Volatility level: low (stable) or high (volatile) based on ATR and Bollinger Bands';

COMMENT ON COLUMN market_regimes.momentum_state IS
'Momentum strength: bullish (strong up), bearish (strong down), or weak (no clear direction)';

COMMENT ON COLUMN market_regimes.full_regime IS
'Full 3D regime string combining all components (e.g., UPTREND_LOWVOL_BULLISH)';

COMMENT ON COLUMN market_regimes.simplified_regime IS
'Simplified practical regime for trading: TREND_UP, TREND_DOWN, RANGE, CHOPPY, NEUTRAL';

COMMENT ON COLUMN market_regimes.confidence IS
'Classification confidence score (0.0-1.0). Higher values indicate stronger regime signals.';

COMMENT ON COLUMN market_regimes.classifier_version IS
'Version of the regime classifier algorithm used for this classification';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- AI query: Find all TREND_UP periods in 2024
-- SELECT symbol, timeframe, open_time, confidence
-- FROM market_regimes
-- WHERE simplified_regime = 'TREND_UP'
--   AND open_time >= '2024-01-01'
-- ORDER BY confidence DESC;

-- AI query: Get regime distribution for BTCUSDT 1h
-- SELECT simplified_regime, COUNT(*) as count
-- FROM market_regimes
-- WHERE symbol = 'BTCUSDT' AND timeframe = '1h'
-- GROUP BY simplified_regime;

-- AI query: Find high-confidence regime transitions
-- SELECT
--   r1.open_time,
--   r1.simplified_regime as from_regime,
--   r2.simplified_regime as to_regime,
--   r1.confidence,
--   r2.confidence
-- FROM market_regimes r1
-- JOIN market_regimes r2
--   ON r1.symbol = r2.symbol
--   AND r1.timeframe = r2.timeframe
--   AND r2.open_time = r1.open_time + INTERVAL '1 hour'
-- WHERE r1.simplified_regime != r2.simplified_regime
--   AND r1.confidence > 0.7
--   AND r2.confidence > 0.7
-- ORDER BY r1.open_time DESC;
