-- ============================================================================
-- Migration: 004_add_error_logs
-- Description: Table for capturing tool/agent errors for debugging
-- ============================================================================

-- ============================================================================
-- CREATE TABLE: error_logs
-- ============================================================================

CREATE TABLE IF NOT EXISTS error_logs (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Context
    source VARCHAR(50) NOT NULL,          -- 'mcp_tool', 'api', 'agent', 'backtest'
    tool_name VARCHAR(100),               -- e.g., 'run_backtest', 'create_strategy'
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,

    -- Error details
    error_type VARCHAR(200) NOT NULL,     -- Exception class name
    error_message TEXT NOT NULL,          -- Full error message
    stack_trace TEXT,                     -- Full traceback

    -- Request context (what was being attempted)
    request_data JSONB,                   -- Parameters that caused the error

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- Index for querying recent errors
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_logs_source ON error_logs(source);
CREATE INDEX IF NOT EXISTS idx_error_logs_tool ON error_logs(tool_name);
