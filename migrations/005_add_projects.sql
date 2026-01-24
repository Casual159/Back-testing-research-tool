-- Migration: Add projects and research events tables
-- Purpose: Store research projects ("save slots") and timeline events

-- ============================================================================
-- CREATE TABLE: projects
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core fields
    name VARCHAR(200) NOT NULL,
    description TEXT,
    thesis TEXT,  -- Core trading hypothesis being researched

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, concluded
    validation_result VARCHAR(50),         -- validated, invalidated, inconclusive

    -- User context from onboarding
    user_preferences JSONB DEFAULT '{}'::jsonb,

    -- Aggregated stats (denormalized for quick access)
    conversation_count INTEGER DEFAULT 0,
    backtest_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CREATE TABLE: research_events
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_events (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Event classification
    event_type VARCHAR(50) NOT NULL,  -- strategy_created, backtest_run, conclusion, note, milestone

    -- Content
    title VARCHAR(200) NOT NULL,
    summary TEXT,

    -- Reference to source entity
    reference_type VARCHAR(50),  -- conversation, backtest_report, strategy
    reference_id UUID,

    -- Rich metadata
    data JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ALTER EXISTING TABLES: Add project_id foreign keys
-- ============================================================================

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

ALTER TABLE backtest_reports
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- projects indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC);

-- research_events indexes
CREATE INDEX IF NOT EXISTS idx_events_project ON research_events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON research_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON research_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_reference ON research_events(reference_type, reference_id);

-- foreign key indexes on existing tables
CREATE INDEX IF NOT EXISTS idx_conversations_project ON conversations(project_id);
CREATE INDEX IF NOT EXISTS idx_reports_project ON backtest_reports(project_id);

-- ============================================================================
-- TRIGGER: Update updated_at on projects
-- ============================================================================

CREATE OR REPLACE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE projects IS
'Research projects - like game save slots. Each project groups related conversations, backtests, and research events under a common hypothesis.';

COMMENT ON TABLE research_events IS
'Timeline events for research log. Tracks significant moments in project lifecycle: strategy creation, backtest runs, conclusions, notes.';

COMMENT ON COLUMN projects.thesis IS
'The core trading hypothesis being researched in this project. E.g., "RSI divergence works better in ranging markets"';

COMMENT ON COLUMN projects.status IS
'Project status: active (in progress), paused (temporarily stopped), concluded (research complete)';

COMMENT ON COLUMN projects.validation_result IS
'Research outcome: validated (hypothesis confirmed), invalidated (hypothesis rejected), inconclusive (needs more data)';

COMMENT ON COLUMN research_events.event_type IS
'Event type: strategy_created, backtest_run, conclusion, note, milestone';

COMMENT ON COLUMN research_events.reference_type IS
'Type of entity this event references: conversation, backtest_report, strategy';

COMMENT ON COLUMN research_events.data IS
'Additional structured data for the event. E.g., for backtest_run: {sharpe_ratio, total_return, ...}';
