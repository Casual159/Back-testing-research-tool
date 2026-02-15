"""baseline_from_sql_migrations

Full schema baseline. Uses CREATE IF NOT EXISTS so it's safe on both:
- Existing DB (no-op — tables already exist)
- Fresh DB (creates everything from scratch)

Captures all tables from SQL migrations 001-005 plus legacy tables.

Revision ID: 3a8136333301
Revises:
Create Date: 2024-02-14

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a8136333301"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # HELPER FUNCTION: update_updated_at_column()
    # Used by triggers on strategies, conversations, projects
    # =========================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # =========================================================================
    # TABLE: candles (OHLCV market data)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS candles (
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            open_time TIMESTAMP NOT NULL,
            "open" NUMERIC NOT NULL,
            high NUMERIC NOT NULL,
            low NUMERIC NOT NULL,
            "close" NUMERIC NOT NULL,
            volume NUMERIC NOT NULL,
            close_time TIMESTAMP NOT NULL,
            quote_volume NUMERIC,
            trades INTEGER,
            PRIMARY KEY (symbol, timeframe, open_time)
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_candles_lookup
        ON candles (symbol, timeframe, open_time DESC);
    """
    )

    # =========================================================================
    # TABLE: market_regimes (regime classification)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS market_regimes (
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            open_time TIMESTAMP NOT NULL,
            trend_state VARCHAR(50),
            volatility_state VARCHAR(50),
            momentum_state VARCHAR(50),
            full_regime VARCHAR(100),
            simplified_regime VARCHAR(50),
            confidence DOUBLE PRECISION,
            classifier_version VARCHAR(20) DEFAULT 'v1.0',
            created_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (symbol, timeframe, open_time)
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_regime_time_range
        ON market_regimes (symbol, timeframe, open_time DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_regime_simplified
        ON market_regimes (simplified_regime, open_time DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_regime_components
        ON market_regimes (trend_state, volatility_state, momentum_state);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_regime_confidence
        ON market_regimes (confidence DESC) WHERE confidence > 0.7;
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_regime_high_quality
        ON market_regimes (simplified_regime, symbol, timeframe, open_time DESC)
        WHERE confidence > 0.7;
    """
    )

    # =========================================================================
    # TABLE: strategies (trading strategy definitions)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS strategies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            class_name VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            parameters JSONB NOT NULL,
            regime_filter JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies(name);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strategies_class ON strategies(class_name);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strategies_metadata
        ON strategies USING GIN (metadata);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strategies_regime_filter
        ON strategies USING GIN (regime_filter);
    """
    )
    op.execute(
        """
        CREATE OR REPLACE TRIGGER update_strategies_updated_at
        BEFORE UPDATE ON strategies
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # =========================================================================
    # TABLE: backtest_results (legacy — used by strategy_storage.py)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS backtest_results (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER,
            strategy_name VARCHAR(100) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            initial_capital NUMERIC NOT NULL,
            commission_rate NUMERIC,
            slippage_rate NUMERIC,
            position_size_pct NUMERIC,
            total_return_pct NUMERIC,
            sharpe_ratio NUMERIC,
            max_drawdown_pct NUMERIC,
            win_rate_pct NUMERIC,
            total_trades INTEGER,
            profit_factor NUMERIC,
            avg_trade_duration_hours NUMERIC,
            equity_curve JSONB,
            trades JSONB,
            regime_stats JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_backtest_strategy
        ON backtest_results(strategy_id);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_backtest_strategy_name
        ON backtest_results(strategy_name);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_backtest_symbol
        ON backtest_results(symbol, timeframe);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_backtest_created
        ON backtest_results(created_at DESC);
    """
    )

    # =========================================================================
    # TABLE: conversations (agent chat history)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            messages JSONB NOT NULL DEFAULT '[]'::jsonb,
            phase VARCHAR(50),
            context JSONB,
            total_tokens INTEGER DEFAULT 0,
            total_cost_usd DECIMAL(10, 6) DEFAULT 0,
            tool_calls_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_created
        ON conversations(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_phase
        ON conversations(phase);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_updated
        ON conversations(updated_at DESC);
    """
    )
    op.execute(
        """
        CREATE OR REPLACE TRIGGER update_conversations_updated_at
        BEFORE UPDATE ON conversations
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # =========================================================================
    # TABLE: backtest_reports (rich reports with AI analysis)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS backtest_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            strategy_name VARCHAR(100) NOT NULL,
            strategy_config JSONB NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            initial_capital DECIMAL(15, 2) NOT NULL DEFAULT 10000,
            total_return_pct DECIMAL(10, 4),
            sharpe_ratio DECIMAL(10, 4),
            max_drawdown_pct DECIMAL(10, 4),
            win_rate_pct DECIMAL(10, 4),
            total_trades INTEGER,
            profit_factor DECIMAL(10, 4),
            calmar_ratio DECIMAL(10, 4),
            sortino_ratio DECIMAL(10, 4),
            recovery_factor DECIMAL(10, 4),
            avg_trade_duration_hours DECIMAL(10, 2),
            best_trade_pct DECIMAL(10, 4),
            worst_trade_pct DECIMAL(10, 4),
            max_consecutive_wins INTEGER,
            max_consecutive_losses INTEGER,
            equity_curve JSONB,
            trades JSONB,
            drawdown_curve JSONB,
            monthly_returns JSONB,
            regime_performance JSONB,
            ai_summary TEXT,
            ai_recommendations JSONB,
            ai_concerns JSONB,
            conversation_id UUID,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_strategy
        ON backtest_reports(strategy_name);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_symbol_timeframe
        ON backtest_reports(symbol, timeframe);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_created
        ON backtest_reports(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_conversation
        ON backtest_reports(conversation_id);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_sharpe
        ON backtest_reports(sharpe_ratio DESC)
        WHERE sharpe_ratio IS NOT NULL;
    """
    )
    # FK to conversations (safe — conversations table created above)
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE backtest_reports
                ADD CONSTRAINT fk_reports_conversation
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """
    )

    # =========================================================================
    # TABLE: agent_suggestions
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_suggestions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
            report_id UUID REFERENCES backtest_reports(id) ON DELETE SET NULL,
            category VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            rationale TEXT,
            priority VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_suggestions_category
        ON agent_suggestions(category);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_suggestions_status
        ON agent_suggestions(status);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_suggestions_priority
        ON agent_suggestions(priority);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_suggestions_created
        ON agent_suggestions(created_at DESC);
    """
    )

    # =========================================================================
    # TABLE: error_logs
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS error_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source VARCHAR(50) NOT NULL,
            tool_name VARCHAR(100),
            conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
            error_type VARCHAR(200) NOT NULL,
            error_message TEXT NOT NULL,
            stack_trace TEXT,
            request_data JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            resolved_at TIMESTAMP,
            resolution_notes TEXT
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_error_logs_created_at
        ON error_logs(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_error_logs_source
        ON error_logs(source);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_error_logs_tool
        ON error_logs(tool_name);
    """
    )

    # =========================================================================
    # TABLE: projects (research projects)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(200) NOT NULL,
            description TEXT,
            thesis TEXT,
            status VARCHAR(50) DEFAULT 'active',
            validation_result VARCHAR(50),
            user_preferences JSONB DEFAULT '{}'::jsonb,
            conversation_count INTEGER DEFAULT 0,
            backtest_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_projects_created
        ON projects(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_projects_updated
        ON projects(updated_at DESC);
    """
    )
    op.execute(
        """
        CREATE OR REPLACE TRIGGER update_projects_updated_at
        BEFORE UPDATE ON projects
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # =========================================================================
    # TABLE: research_events (project timeline)
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS research_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            summary TEXT,
            reference_type VARCHAR(50),
            reference_id UUID,
            data JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_project
        ON research_events(project_id);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_type
        ON research_events(event_type);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_created
        ON research_events(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_reference
        ON research_events(reference_type, reference_id);
    """
    )

    # =========================================================================
    # ALTER: Add project_id to conversations and backtest_reports
    # =========================================================================
    op.execute(
        """
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS project_id UUID
        REFERENCES projects(id) ON DELETE SET NULL;
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_project
        ON conversations(project_id);
    """
    )
    op.execute(
        """
        ALTER TABLE backtest_reports
        ADD COLUMN IF NOT EXISTS project_id UUID
        REFERENCES projects(id) ON DELETE SET NULL;
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_project
        ON backtest_reports(project_id);
    """
    )

    # =========================================================================
    # LEGACY TABLES: research_insights, research_queries, recent_insights
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS research_insights (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP NOT NULL,
            query_text TEXT NOT NULL,
            insight_type VARCHAR(50) NOT NULL,
            symbol VARCHAR(20),
            timeframe VARCHAR(10),
            insight_summary TEXT NOT NULL,
            insight_detail JSONB NOT NULL,
            metadata JSONB
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_insights_created_at
        ON research_insights(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_insights_symbol
        ON research_insights(symbol);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_insights_type
        ON research_insights(insight_type);
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS research_queries (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP NOT NULL,
            query_text TEXT NOT NULL,
            query_type VARCHAR(50),
            parameters JSONB,
            response_summary TEXT,
            execution_time_ms INTEGER
        );
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_queries_created_at
        ON research_queries(created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_queries_type
        ON research_queries(query_type);
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS recent_insights (
            id INTEGER,
            created_at TIMESTAMP,
            query_text TEXT,
            insight_type VARCHAR(50),
            symbol VARCHAR(20),
            timeframe VARCHAR(10),
            insight_summary TEXT,
            insight_detail JSONB,
            metadata JSONB
        );
    """
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Cannot rollback baseline migration. " "Database was initialized with SQL migrations."
    )
