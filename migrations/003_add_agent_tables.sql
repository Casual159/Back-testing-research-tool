-- Migration: Add tables for AI agent and backtest reports
-- Purpose: Store conversation history, backtest reports, and agent suggestions

-- ============================================================================
-- CREATE TABLE: backtest_reports
-- ============================================================================

CREATE TABLE IF NOT EXISTS backtest_reports (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Strategy reference
    strategy_name VARCHAR(100) NOT NULL,
    strategy_config JSONB NOT NULL,  -- Snapshot of strategy at time of backtest

    -- Dataset parameters
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15, 2) NOT NULL DEFAULT 10000,

    -- Core metrics
    total_return_pct DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown_pct DECIMAL(10, 4),
    win_rate_pct DECIMAL(10, 4),
    total_trades INTEGER,
    profit_factor DECIMAL(10, 4),

    -- Extended metrics
    calmar_ratio DECIMAL(10, 4),
    sortino_ratio DECIMAL(10, 4),
    recovery_factor DECIMAL(10, 4),
    avg_trade_duration_hours DECIMAL(10, 2),
    best_trade_pct DECIMAL(10, 4),
    worst_trade_pct DECIMAL(10, 4),
    max_consecutive_wins INTEGER,
    max_consecutive_losses INTEGER,

    -- Data for visualizations (stored as JSONB for flexibility)
    equity_curve JSONB,           -- [{time, value}, ...]
    trades JSONB,                 -- [{entry_time, exit_time, entry_price, exit_price, pnl_pct}, ...]
    drawdown_curve JSONB,         -- [{time, drawdown_pct}, ...]
    monthly_returns JSONB,        -- {YYYY-MM: return_pct, ...}

    -- Regime analysis
    regime_performance JSONB,     -- {TREND_UP: {trades, return, win_rate}, ...}

    -- AI interpretation (filled by agent)
    ai_summary TEXT,
    ai_recommendations JSONB,     -- [recommendation1, recommendation2, ...]
    ai_concerns JSONB,            -- [concern1, concern2, ...]

    -- Metadata
    conversation_id UUID,         -- Link to conversation that created this
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CREATE TABLE: conversations
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conversation data
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{role, content, tool_calls, timestamp}, ...]

    -- Agent state
    phase VARCHAR(50),            -- STRATEGY_DESIGN, STRATEGY_VALIDATION, DATA_SELECTION, etc.
    context JSONB,                -- {proposed_strategy, selected_data, etc.}

    -- Usage tracking
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0,
    tool_calls_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CREATE TABLE: agent_suggestions
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_suggestions (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    report_id UUID REFERENCES backtest_reports(id) ON DELETE SET NULL,

    -- Suggestion content
    category VARCHAR(50) NOT NULL,  -- indicator, metric, visualization, strategy, data, other
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT,                 -- Why agent thinks this would help

    -- Priority/status
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high
    status VARCHAR(20) DEFAULT 'pending',   -- pending, planned, in_progress, done, rejected

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- backtest_reports indexes
CREATE INDEX idx_reports_strategy ON backtest_reports(strategy_name);
CREATE INDEX idx_reports_symbol_timeframe ON backtest_reports(symbol, timeframe);
CREATE INDEX idx_reports_created ON backtest_reports(created_at DESC);
CREATE INDEX idx_reports_conversation ON backtest_reports(conversation_id);
CREATE INDEX idx_reports_sharpe ON backtest_reports(sharpe_ratio DESC) WHERE sharpe_ratio IS NOT NULL;

-- conversations indexes
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_phase ON conversations(phase);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);

-- agent_suggestions indexes
CREATE INDEX idx_suggestions_category ON agent_suggestions(category);
CREATE INDEX idx_suggestions_status ON agent_suggestions(status);
CREATE INDEX idx_suggestions_priority ON agent_suggestions(priority);
CREATE INDEX idx_suggestions_created ON agent_suggestions(created_at DESC);

-- ============================================================================
-- TRIGGER: Update updated_at on conversations
-- ============================================================================

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FOREIGN KEY: Link reports to conversations
-- ============================================================================

ALTER TABLE backtest_reports
    ADD CONSTRAINT fk_reports_conversation
    FOREIGN KEY (conversation_id)
    REFERENCES conversations(id)
    ON DELETE SET NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE backtest_reports IS
'Persisted backtest results with metrics, trade data, and AI interpretation. Each report is a complete snapshot of a backtest run.';

COMMENT ON TABLE conversations IS
'Agent conversation history. Stores full message history, current phase, and usage metrics.';

COMMENT ON TABLE agent_suggestions IS
'Feature suggestions generated by the agent during analysis. Used to track ideas for tool improvements.';

COMMENT ON COLUMN backtest_reports.strategy_config IS
'Complete strategy configuration snapshot at time of backtest. Includes parameters, regime_filter, etc.';

COMMENT ON COLUMN backtest_reports.ai_summary IS
'Agent-generated natural language summary of backtest results and key insights.';

COMMENT ON COLUMN conversations.phase IS
'Current agent workflow phase: STRATEGY_DESIGN, STRATEGY_VALIDATION, DATA_SELECTION, BACKTEST_EXECUTION, RESULTS_ANALYSIS, COMPLETE';

COMMENT ON COLUMN conversations.context IS
'Agent working memory - stores proposed_strategy, selected_dataset, pending_confirmations, etc.';

COMMENT ON COLUMN agent_suggestions.category IS
'Suggestion category: indicator (new technical indicator), metric (new performance metric), visualization (new chart/view), strategy (strategy improvement), data (data source), other';
