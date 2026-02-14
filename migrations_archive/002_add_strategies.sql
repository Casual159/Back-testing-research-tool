-- Migration: Add strategies table for storing trading strategy definitions
-- Purpose: Persist both built-in and user-created composite strategies
-- Related: Supports agent tools for list_strategies, create_strategy, run_backtest

-- ============================================================================
-- CREATE TABLE: strategies
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategies (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Basic info
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,

    -- Strategy type
    strategy_type VARCHAR(50) NOT NULL,  -- 'builtin' | 'composite'

    -- For builtin strategies: store the class name
    builtin_class VARCHAR(50),  -- 'MovingAverageCrossover', 'RSIReversal', etc.

    -- For composite strategies: store the logic as JSON
    entry_logic JSONB,
    exit_logic JSONB,

    -- Parameters (for any strategy type)
    parameters JSONB DEFAULT '{}',

    -- Context filters - regime awareness
    regime_filter TEXT[],  -- ['TREND_UP', 'RANGE'] - simplified regimes
    sub_regime_filter JSONB,  -- {"trend": ["uptrend"], "volatility": ["low"]}

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_strategy_type CHECK (
        strategy_type IN ('builtin', 'composite')
    ),
    CONSTRAINT builtin_has_class CHECK (
        strategy_type != 'builtin' OR builtin_class IS NOT NULL
    ),
    CONSTRAINT composite_has_logic CHECK (
        strategy_type != 'composite' OR (entry_logic IS NOT NULL AND exit_logic IS NOT NULL)
    )
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies(name);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies(is_active) WHERE is_active = true;

-- ============================================================================
-- INSERT BUILT-IN STRATEGIES
-- ============================================================================

INSERT INTO strategies (name, description, strategy_type, builtin_class, parameters) VALUES
(
    'MA Crossover',
    'Trend-following strategy using moving average crossovers. Generates BUY when fast MA crosses above slow MA (golden cross), SELL when fast MA crosses below (death cross).',
    'builtin',
    'MovingAverageCrossover',
    '{"fast_period": 20, "slow_period": 50, "ma_type": "SMA"}'
),
(
    'RSI Reversal',
    'Mean-reversion strategy using RSI overbought/oversold levels. BUY when RSI drops below oversold threshold, SELL when RSI rises above overbought threshold.',
    'builtin',
    'RSIReversal',
    '{"rsi_period": 14, "oversold": 30, "overbought": 70}'
),
(
    'Bollinger Bands',
    'Volatility-based mean-reversion strategy. BUY when price touches lower band, SELL when price touches upper band.',
    'builtin',
    'BollingerBands',
    '{"period": 20, "num_std": 2.0, "touch_threshold": 0.01}'
),
(
    'MACD Cross',
    'Momentum strategy using MACD crossovers. BUY when MACD crosses above signal line, SELL when MACD crosses below.',
    'builtin',
    'MACDCross',
    '{"fast_period": 12, "slow_period": 26, "signal_period": 9}'
)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- CREATE TABLE: backtest_results
-- ============================================================================

CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,

    -- Reference to strategy
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    strategy_name VARCHAR(100) NOT NULL,  -- Denormalized for convenience

    -- Data context
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,

    -- Backtest config
    initial_capital DECIMAL(20, 2) NOT NULL,
    commission_rate DECIMAL(10, 6),
    slippage_rate DECIMAL(10, 6),
    position_size_pct DECIMAL(5, 4),

    -- Results - Key Metrics
    total_return_pct DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown_pct DECIMAL(10, 4),
    win_rate_pct DECIMAL(10, 4),
    total_trades INTEGER,
    profit_factor DECIMAL(10, 4),
    avg_trade_duration_hours DECIMAL(10, 2),

    -- Results - Full data (for charts and detailed analysis)
    equity_curve JSONB,  -- [[timestamp, value], ...]
    trades JSONB,        -- [{entry_time, exit_time, pnl, ...}, ...]

    -- Regime statistics
    regime_stats JSONB,  -- {regime_filter, signals_skipped, ...}

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES for backtest_results
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_strategy_name ON backtest_results(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_symbol ON backtest_results(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_backtest_created ON backtest_results(created_at DESC);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE strategies IS
'Trading strategy definitions - both built-in and user-created composite strategies';

COMMENT ON COLUMN strategies.strategy_type IS
'builtin = pre-defined Python class, composite = user-created from LogicTree';

COMMENT ON COLUMN strategies.regime_filter IS
'List of allowed simplified regimes: TREND_UP, TREND_DOWN, RANGE, CHOPPY, NEUTRAL';

COMMENT ON COLUMN strategies.sub_regime_filter IS
'Filter by sub-regime components: {"trend": ["uptrend"], "volatility": ["low"], "momentum": ["bullish"]}';

COMMENT ON TABLE backtest_results IS
'Historical backtest results for analysis and comparison';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- List all active strategies
-- SELECT name, strategy_type, description, regime_filter
-- FROM strategies
-- WHERE is_active = true
-- ORDER BY name;

-- Get strategy with parameters
-- SELECT name, parameters, regime_filter
-- FROM strategies
-- WHERE name = 'RSI Reversal';

-- Find strategies suitable for RANGE regime
-- SELECT name, description
-- FROM strategies
-- WHERE 'RANGE' = ANY(regime_filter)
--    OR regime_filter IS NULL;

-- Get recent backtest results for a strategy
-- SELECT strategy_name, symbol, total_return_pct, sharpe_ratio, win_rate_pct
-- FROM backtest_results
-- WHERE strategy_name = 'RSI Reversal'
-- ORDER BY created_at DESC
-- LIMIT 10;
