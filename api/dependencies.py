"""
FastAPI dependency injection providers.

These dependencies are used across API endpoints to provide
common services like database connections, configuration, etc.
"""

from typing import Generator

from fastapi import Depends, HTTPException, Request

from config.config import load_config
from core.data.storage import PostgresStorage
from core.logging_config import get_logger

logger = get_logger(__name__)

# Global config - loaded once at startup
_app_config = None


def get_config() -> dict:
    """
    Get application configuration.

    This is loaded once at startup and cached.
    Use this instead of calling load_config() everywhere.

    Usage:
        @app.get("/endpoint")
        def endpoint(config: dict = Depends(get_config)):
            db_config = config['database']
    """
    global _app_config
    if _app_config is None:
        _app_config = load_config()
    return _app_config  # type: ignore[no-any-return]


def get_db_storage(config: dict = Depends(get_config)) -> Generator[PostgresStorage, None, None]:
    """
    Provide a PostgresStorage instance with automatic cleanup.

    The connection is automatically closed after the request completes,
    even if an error occurs.

    Usage:
        @app.get("/endpoint")
        def endpoint(storage: PostgresStorage = Depends(get_db_storage)):
            data = storage.get_data_stats()
            return data

    Benefits:
    - Automatic connection cleanup (no forgotten close())
    - Easy to mock in tests
    - Consistent error handling
    """
    storage = PostgresStorage(config["database"])
    try:
        yield storage
    except Exception as e:
        logger.error("database_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        # Always close connection
        if hasattr(storage, "conn") and storage.conn:
            storage.conn.close()


def get_request_id(request: Request) -> str:
    """
    Get the current request ID.

    The request ID is set by RequestIDMiddleware and can be used
    for logging and debugging.

    Usage:
        @app.get("/endpoint")
        def endpoint(request_id: str = Depends(get_request_id)):
            logger.info("processing", request_id=request_id)
    """
    return getattr(request.state, "request_id", "unknown")


def require_api_key(request: Request, config: dict = Depends(get_config)) -> str:
    """
    Dependency for endpoints that require API key authentication.

    Usage:
        @app.get("/admin/endpoint")
        def admin_endpoint(api_key: str = Depends(require_api_key)):
            # Only reachable with valid API key
            pass

    Returns:
        The validated API key

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    # Get API key from header
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Include X-API-Key header.")

    # Get expected API key from config
    expected_key = config.get("api_key")

    # If no API key is configured, allow (for development)
    if not expected_key:
        logger.warning("no_api_key_configured", message="API key check skipped")
        return str(api_key)

    # Validate API key
    if api_key != expected_key:
        logger.warning("invalid_api_key", provided_key=api_key[:8] + "...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return str(api_key)
