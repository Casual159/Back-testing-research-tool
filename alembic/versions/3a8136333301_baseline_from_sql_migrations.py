"""baseline_from_sql_migrations

This migration represents the current state of the database after applying
all SQL migrations from the migrations/ folder:
- 001_add_market_regimes.sql
- 002_add_strategies.sql
- 003_add_agent_tables.sql
- 004_add_error_logs.sql
- 005_add_projects.sql

No actual changes are applied here - this is just a baseline for future
Alembic migrations.

Revision ID: 3a8136333301
Revises:
Create Date: 2024-02-14

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3a8136333301"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Database already has all tables from SQL migrations 001-005.

    Current schema includes:
    - candles (OHLCV data)
    - market_regimes (regime detection)
    - strategies (trading strategies)
    - backtest_reports (backtest results)
    - conversations (agent chat history)
    - suggestions (feature suggestions)
    - error_logs (error tracking)
    - projects (research projects)
    - timeline_events (project timeline)
    - user_preferences (onboarding preferences)

    This migration does nothing - it's just a baseline marker.
    All future schema changes should be done via Alembic migrations.
    """
    pass


def downgrade() -> None:
    """
    Cannot rollback past this point - this represents the initial state
    from SQL migrations.
    """
    raise NotImplementedError(
        "Cannot rollback baseline migration. " "Database was initialized with SQL migrations."
    )
