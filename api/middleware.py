"""
FastAPI middleware for request tracking and error handling.
"""

import time
import traceback
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging_config import bind_context, clear_context, get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique request ID to each request for tracing.

    The request ID is:
    - Generated for each request (UUID4)
    - Added to response headers as X-Request-ID
    - Bound to logger context for all logs in this request
    - Accessible via request.state.request_id
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind to logger context so all logs include it
        bind_context(request_id=request_id)

        try:
            # Process request
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            return response

        except Exception as e:
            # Log unhandled errors
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc(),
            )
            raise

        finally:
            # Clear context after request
            clear_context()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler for all unhandled exceptions.

    Catches exceptions that weren't handled by route handlers and returns
    a consistent error response with request ID for debugging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except Exception as e:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", "unknown")

            # Log the error
            logger.error(
                "unhandled_exception",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                stack_trace=traceback.format_exc(),
                request_id=request_id,
            )

            # Return error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                },
                headers={"X-Request-ID": request_id},
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all incoming requests with details.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log incoming request
        logger.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
        )

        return await call_next(request)
