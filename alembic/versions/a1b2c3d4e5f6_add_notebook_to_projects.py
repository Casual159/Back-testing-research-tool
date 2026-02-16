"""add notebook column to projects

Add JSONB notebook column to projects table for storing
block-based research notes (text, backtest refs, agent insights).

Revision ID: a1b2c3d4e5f6
Revises: 7aa7c245dbff
Create Date: 2026-02-16 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7aa7c245dbff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS notebook JSONB DEFAULT '[]'::jsonb;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE projects
        DROP COLUMN IF EXISTS notebook;
    """)
