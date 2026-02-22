"""add users table and multi-tenancy columns

Create users table for authentication (Google OAuth + email/password).
Add user_id foreign key to projects, conversations, backtest_reports
for multi-tenant data isolation.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-22 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(200),
            image_url TEXT,
            password_hash VARCHAR(255),
            provider VARCHAR(50) NOT NULL DEFAULT 'credentials',
            provider_account_id VARCHAR(255),
            email_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Indexes for users
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_provider
        ON users(provider, provider_account_id);
    """)

    # Trigger for updated_at
    op.execute("""
        CREATE OR REPLACE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # Add user_id FK to projects
    op.execute("""
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
    """)

    # Add user_id FK to conversations
    op.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
    """)

    # Add user_id FK to backtest_reports
    op.execute("""
        ALTER TABLE backtest_reports
        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reports_user_id ON backtest_reports(user_id);
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE backtest_reports DROP COLUMN IF EXISTS user_id;")
    op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS user_id;")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS user_id;")
    op.execute("DROP TABLE IF EXISTS users;")
