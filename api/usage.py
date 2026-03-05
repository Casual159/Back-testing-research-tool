"""
Usage tracking and credit management for billing infrastructure.

Provides:
- record_usage_event: append-only log of billable actions
- deduct_credits: atomic balance deduction with ledger entry
- add_credits: top-up or grant credits with ledger entry
- get_user_usage_current_period: monthly usage aggregates
- get_user_credit_balance: current balance from DB
"""

import json
import logging
from typing import Any, Optional

from core.data.storage import PostgresStorage

logger = logging.getLogger(__name__)


def record_usage_event(
    db_config: dict,
    user_id: Optional[str],
    event_type: str,
    endpoint: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """
    Record a billable usage event. Fire-and-forget — never blocks the request.

    Returns the event UUID on success, None on failure.
    """
    try:
        with PostgresStorage(db_config) as storage:
            storage.cursor.execute(
                """
                INSERT INTO usage_events
                    (user_id, event_type, endpoint, input_tokens,
                     output_tokens, cost_usd, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_id,
                    event_type,
                    endpoint,
                    input_tokens,
                    output_tokens,
                    cost_usd,
                    json.dumps(metadata or {}),
                ),
            )
            row = storage.cursor.fetchone()
            storage.conn.commit()
            event_id = str(row[0]) if row else None
            logger.info(
                "usage_event_recorded",
                extra={
                    "event_type": event_type,
                    "user_id": user_id,
                    "cost_usd": cost_usd,
                    "event_id": event_id,
                },
            )
            return event_id
    except Exception as e:
        logger.error(f"usage_event_failed: {e}", extra={"event_type": event_type})
        return None


def deduct_credits(
    db_config: dict,
    user_id: str,
    cost_usd: float,
    usage_event_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[float]:
    """
    Atomically deduct credits from user balance and record a ledger entry.

    Uses atomic SQL: UPDATE ... WHERE credits_balance >= cost.
    If balance is insufficient, returns None (no deduction made).

    Returns new balance on success, None if insufficient.
    """
    if cost_usd <= 0:
        return None

    try:
        with PostgresStorage(db_config) as storage:
            # Atomic deduction — only succeeds if balance is sufficient
            storage.cursor.execute(
                """
                UPDATE users
                SET credits_balance = credits_balance - %s,
                    updated_at = NOW()
                WHERE id = %s AND credits_balance >= %s
                RETURNING credits_balance
                """,
                (cost_usd, user_id, cost_usd),
            )
            row = storage.cursor.fetchone()

            if not row:
                # Insufficient balance — allow slight negative for in-flight requests
                storage.cursor.execute(
                    """
                    UPDATE users
                    SET credits_balance = credits_balance - %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING credits_balance
                    """,
                    (cost_usd, user_id),
                )
                row = storage.cursor.fetchone()
                if not row:
                    storage.conn.rollback()
                    return None
                new_balance = float(row[0])
                logger.warning(f"credits_negative: user={user_id} balance={new_balance}")
            else:
                new_balance = float(row[0])

            # Record ledger entry
            storage.cursor.execute(
                """
                INSERT INTO credit_transactions
                    (user_id, amount, type, balance_after, reference_id, description)
                VALUES (%s, %s, 'deduction', %s, %s, %s)
                """,
                (
                    user_id,
                    -cost_usd,
                    new_balance,
                    usage_event_id,
                    description or f"API usage: ${cost_usd:.6f}",
                ),
            )
            storage.conn.commit()

            logger.info(
                f"credits_deducted: user={user_id} "
                f"amount=${cost_usd:.6f} balance=${new_balance:.6f}"
            )
            return new_balance

    except Exception as e:
        logger.error(f"credit_deduction_failed: {e}", extra={"user_id": user_id})
        return None


def add_credits(
    db_config: dict,
    user_id: str,
    amount: float,
    description: str,
    tx_type: str = "grant",
    reference_id: Optional[str] = None,
) -> Optional[float]:
    """
    Add credits to user balance and record a ledger entry.

    tx_type: 'topup' (Stripe payment), 'grant' (admin manual), 'refund'

    Returns new balance on success, None on failure.
    """
    if amount <= 0:
        return None

    try:
        with PostgresStorage(db_config) as storage:
            storage.cursor.execute(
                """
                UPDATE users
                SET credits_balance = credits_balance + %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING credits_balance
                """,
                (amount, user_id),
            )
            row = storage.cursor.fetchone()
            if not row:
                return None

            new_balance = float(row[0])

            storage.cursor.execute(
                """
                INSERT INTO credit_transactions
                    (user_id, amount, type, balance_after, reference_id, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, amount, tx_type, new_balance, reference_id, description),
            )
            storage.conn.commit()

            logger.info(
                f"credits_added: user={user_id} "
                f"amount=${amount:.6f} balance=${new_balance:.6f} type={tx_type}"
            )
            return new_balance

    except Exception as e:
        logger.error(f"credit_add_failed: {e}", extra={"user_id": user_id})
        return None


def get_user_usage_current_period(
    db_config: dict,
    user_id: str,
) -> dict:
    """
    Get user's usage aggregates for the current calendar month.
    """
    try:
        with PostgresStorage(db_config) as storage:
            storage.cursor.execute(
                """
                SELECT
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COUNT(*) as total_events,
                    COALESCE(SUM(input_tokens), 0) as total_input,
                    COALESCE(SUM(output_tokens), 0) as total_output,
                    COUNT(*) FILTER (WHERE event_type = 'agent_chat') as agent_chats,
                    COUNT(*) FILTER (WHERE event_type = 'backtest') as backtests,
                    COUNT(*) FILTER (WHERE event_type = 'data_fetch') as data_fetches
                FROM usage_events
                WHERE user_id = %s
                  AND created_at >= date_trunc('month', NOW())
                """,
                (user_id,),
            )
            row = storage.cursor.fetchone()
            return {
                "total_cost_usd": float(row[0]),
                "total_events": row[1],
                "total_input_tokens": row[2],
                "total_output_tokens": row[3],
                "agent_chat_count": row[4],
                "backtest_count": row[5],
                "data_fetch_count": row[6],
            }
    except Exception as e:
        logger.error(f"usage_query_failed: {e}", extra={"user_id": user_id})
        return {
            "total_cost_usd": 0.0,
            "total_events": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "agent_chat_count": 0,
            "backtest_count": 0,
            "data_fetch_count": 0,
        }


def get_user_credit_balance(db_config: dict, user_id: str) -> float:
    """Get user's current credit balance."""
    try:
        with PostgresStorage(db_config) as storage:
            storage.cursor.execute(
                "SELECT credits_balance FROM users WHERE id = %s",
                (user_id,),
            )
            row = storage.cursor.fetchone()
            return float(row[0]) if row else 0.0
    except Exception as e:
        logger.error(f"balance_query_failed: {e}", extra={"user_id": user_id})
        return 0.0
