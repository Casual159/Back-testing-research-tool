"""add_strategy_config_to_backtest_reports

Reconcile production schema differences.
The production DB was created from SQL migrations that may have
different column sets than the baseline Alembic migration expects.

This migration adds any missing columns using IF NOT EXISTS / safe checks.

Revision ID: 7aa7c245dbff
Revises: 3a8136333301
Create Date: 2026-02-15 20:25:21.587516

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7aa7c245dbff"
down_revision: Union[str, Sequence[str], None] = "3a8136333301"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # backtest_reports: add strategy_config if missing
    # =========================================================================
    op.execute("""
        ALTER TABLE backtest_reports
        ADD COLUMN IF NOT EXISTS strategy_config JSONB DEFAULT '{}'::jsonb;
    """)

    # =========================================================================
    # strategies: add columns from both old and new schemas
    # Ensures table works with both strategy_storage.py and api/main.py
    # =========================================================================

    # Old schema columns (from 002_add_strategies.sql)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS strategy_type VARCHAR(50) DEFAULT 'builtin';
    """)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS builtin_class VARCHAR(100);
    """)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS entry_logic JSONB;
    """)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS exit_logic JSONB;
    """)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS sub_regime_filter JSONB;
    """)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
    """)

    # New schema columns (from 002_add_strategies_table.sql)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS class_name VARCHAR(100);
    """)
    op.execute("""
        ALTER TABLE strategies
        ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
    """)

    # Backfill: set class_name from builtin_class where missing
    op.execute("""
        UPDATE strategies
        SET class_name = builtin_class
        WHERE class_name IS NULL AND builtin_class IS NOT NULL;
    """)

    # Backfill: set strategy_type from class_name where missing
    op.execute("""
        UPDATE strategies
        SET strategy_type = CASE
            WHEN class_name = 'CompositeStrategy' THEN 'composite'
            ELSE 'builtin'
        END
        WHERE strategy_type IS NULL;
    """)

    # Backfill: set builtin_class from class_name where missing
    op.execute("""
        UPDATE strategies
        SET builtin_class = class_name
        WHERE builtin_class IS NULL
          AND class_name IS NOT NULL
          AND class_name != 'CompositeStrategy';
    """)


def downgrade() -> None:
    # These are additive changes, safe to leave in place
    pass
