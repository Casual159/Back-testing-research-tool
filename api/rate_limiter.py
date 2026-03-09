"""
Enforcement layer for billing — checks account status and credit balance.

Provides FastAPI dependencies that gate expensive endpoints:
- require_active_account: checks account_status == 'active' and credits > threshold
- Unauthenticated (MCP/internal agent) calls pass through freely
"""

import logging
import os
from typing import Optional

from fastapi import HTTPException, Request

from api.usage import get_user_credit_balance

logger = logging.getLogger(__name__)

# Kill switch: set BILLING_ENABLED=false to bypass all billing checks.
BILLING_ENABLED = os.getenv("BILLING_ENABLED", "false").lower() in ("true", "1", "yes")

# Minimum balance required to start an expensive operation.
MIN_BALANCE_THRESHOLD = 0.01


def _get_user_account_status(db_config: dict, user_id: str) -> Optional[str]:
    """Fetch user's account_status from DB."""
    from core.data.storage import PostgresStorage

    try:
        with PostgresStorage(db_config) as storage:
            storage.cursor.execute(
                "SELECT account_status FROM users WHERE id = %s",
                (user_id,),
            )
            row = storage.cursor.fetchone()
            return str(row[0]) if row else None
    except Exception as e:
        logger.error(f"account_status_check_failed: {e}")
        return None


def require_active_account():
    """
    FastAPI dependency that enforces account status and credit balance.

    Usage:
        @app.post("/api/agent/chat/stream")
        async def agent_chat_stream(
            body: AgentChatRequest,
            http_request: Request = None,
            _auth: None = Depends(require_active_account()),
        ):

    Behavior:
    - No user (MCP/internal agent call): passes through (no enforcement)
    - User with account_status != 'active': 403
    - User with credits_balance <= threshold: 402
    - User with active account + sufficient balance: passes through
    """
    from config.config import load_config

    async def _check(request: Request):
        if not BILLING_ENABLED:
            return None

        from api.dependencies import get_optional_user

        user = get_optional_user(request)

        if user is None:
            # MCP or internal agent call — no user to enforce against.
            # The agent's execute_tool() calls endpoints via localhost
            # without auth headers. Blocking these would break agent
            # functionality. Cost is captured at the agent chat level.
            return None

        app_config = load_config()
        db_config = app_config["database"]

        # Check account status
        status = _get_user_account_status(db_config, user["id"])
        if status != "active":
            logger.warning(f"account_not_active: user={user['id']} status={status}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "account_not_active",
                    "status": status,
                    "message": (
                        "Your account is not active. "
                        "Please enter an invite code or contact the administrator."
                    ),
                },
            )

        # Check credit balance
        balance = get_user_credit_balance(db_config, user["id"])
        if balance < MIN_BALANCE_THRESHOLD:
            logger.warning(f"insufficient_credits: user={user['id']} balance={balance}")
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "balance": balance,
                    "message": ("Insufficient credits. " "Please top up your balance to continue."),
                },
            )

        return None

    return _check
