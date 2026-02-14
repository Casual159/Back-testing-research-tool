"""
Structured logging configuration using structlog.

Provides JSON-formatted logs with context (request IDs, user IDs, etc.)
for better debugging and log aggregation.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application-wide context to logs."""
    event_dict["app"] = "backtesting-research-tool"
    event_dict["env"] = "development"  # TODO: Read from ENV
    return event_dict


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON logs. If False, use human-readable console format.
    """
    # Determine processors based on output format
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    if json_logs:
        # Production: JSON logs for aggregation (Datadog, Logtail, etc.)
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: Human-readable console logs with colors
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("user_logged_in", user_id=123, ip="1.2.3.4")
        logger.error("payment_failed", amount=99.99, error=str(e))
    """
    return structlog.get_logger(name)


# Convenience function for binding context
def bind_context(**kwargs: Any) -> None:
    """
    Bind context that will be added to all subsequent log messages in this scope.

    Example:
        # In middleware
        bind_context(request_id="abc-123", user_id=456)

        # All logs from this point will include request_id and user_id
        logger.info("processing_request")  # Includes request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
