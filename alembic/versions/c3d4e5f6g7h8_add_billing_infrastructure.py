"""add billing infrastructure: usage_events, invites, credit_transactions

Create tables for billing/paywall system:
- usage_events: append-only log of every billable action
- invites: invite-only access control codes
- credit_transactions: double-entry ledger for credit balance changes
- users columns: credits_balance, account_status, invite_id, stripe_customer_id

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-02 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # 1. usage_events — append-only audit log of every billable action
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            event_type VARCHAR(50) NOT NULL,
            endpoint VARCHAR(200) NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cost_usd DECIMAL(10, 6) DEFAULT 0,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_usage_events_user_id
        ON usage_events(user_id);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_usage_events_user_created
        ON usage_events(user_id, created_at DESC);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_usage_events_monthly
        ON usage_events(user_id, event_type, created_at)
        WHERE user_id IS NOT NULL;
    """
    )

    # =========================================================================
    # 2. invites — invite-only access control
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS invites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code VARCHAR(32) NOT NULL UNIQUE,
            created_by UUID REFERENCES users(id),
            email VARCHAR(255),
            used_by UUID REFERENCES users(id),
            used_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_invites_code ON invites(code);
    """
    )

    # =========================================================================
    # 3. credit_transactions — double-entry ledger
    # =========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount DECIMAL(10, 6) NOT NULL,
            type VARCHAR(20) NOT NULL,
            balance_after DECIMAL(10, 6) NOT NULL,
            reference_id UUID,
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_created
        ON credit_transactions(user_id, created_at DESC);
    """
    )

    # =========================================================================
    # 4. New columns on users table
    # =========================================================================
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS credits_balance DECIMAL(10, 6) NOT NULL DEFAULT 0;
    """
    )

    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS account_status VARCHAR(20) NOT NULL DEFAULT 'pending';
    """
    )

    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS invite_id UUID REFERENCES invites(id);
    """
    )

    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_account_status ON users(account_status);
    """
    )

    # Set existing users to 'active' so they don't get locked out
    op.execute(
        """
        UPDATE users SET account_status = 'active' WHERE account_status = 'pending';
    """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS stripe_customer_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS invite_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS account_status;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS credits_balance;")
    op.execute("DROP TABLE IF EXISTS credit_transactions;")
    op.execute("DROP TABLE IF EXISTS invites;")
    op.execute("DROP TABLE IF EXISTS usage_events;")
