"""
FastAPI Backend for Backtesting Research Tool
Provides REST API endpoints for the Next.js frontend
"""

import inspect
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Structured logging
from core.logging_config import get_logger, setup_logging  # noqa: E402

# Setup logging first
setup_logging(log_level="INFO", json_logs=False)  # Set json_logs=True for production
logger = get_logger(__name__)

# Import middleware
from api.middleware import (  # noqa: E402
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
)

# Import schemas (new validated models)
from api.schemas import (  # noqa: E402
    AgentChatRequest,
    BacktestRequest,
    BacktestResponse,
    CreateEventRequest,
    CreateProjectRequest,
    CreateStrategyRequest,
    DataFetchRequest,
    DataFetchResponse,
    LogErrorRequest,
    OnboardingPreferencesRequest,
    StrategyResponse,
    TradeResult,
    UpdateProjectRequest,
)

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from config.config import load_config  # noqa: E402
from core.data.bulk_fetcher import BinanceBulkFetcher  # noqa: E402
from core.data.storage import PostgresStorage  # noqa: E402
from core.indicators.regime import detect_market_regimes  # noqa: E402

# from core.data.strategy_storage import StrategyStorage  # Deprecated - using new strategies table
from core.indicators.technical import add_all_indicators  # noqa: E402

app = FastAPI(
    title="Backtesting Research Tool API",
    description="REST API for cryptocurrency backtesting platform with AI research agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware (order matters - first added = outermost)
app.add_middleware(ErrorHandlerMiddleware)  # Catch all errors
app.add_middleware(RequestIDMiddleware)  # Add request IDs
app.add_middleware(LoggingMiddleware)  # Log requests

# CORS configuration for Next.js frontend
_cors_origins = [
    "http://localhost:3000",  # Next.js dev server
]
_extra_origin = os.environ.get("CORS_ORIGIN")
if _extra_origin:
    _cors_origins.append(_extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
config = load_config()

# Configure conversation storage with DB access
try:
    from agent.core import ConversationStorage

    ConversationStorage.configure(config["database"])
except Exception as e:
    print(f"[WARNING] Could not configure ConversationStorage DB: {e}")

# =============================================================================
# PARAMETER NORMALIZATION FOR STRATEGIES
# =============================================================================

# Mapping of common parameter aliases to canonical names
PARAMETER_ALIASES = {
    # RSI
    "oversold_level": "oversold",
    "overbought_level": "overbought",
    "rsi_oversold": "oversold",
    "rsi_overbought": "overbought",
    # MA
    "short_period": "fast_period",
    "long_period": "slow_period",
    # General
    "std_dev": "num_std",
    "std": "num_std",
}


def log_error_to_db(
    source: str,
    error_type: str,
    error_message: str,
    tool_name: str = None,
    request_data: Dict[str, Any] = None,
    stack_trace: str = None,
    conversation_id: str = None,
) -> None:
    """Log error to error_logs table for debugging."""
    try:
        with PostgresStorage(config["database"]) as storage:
            storage.cursor.execute(
                """
                INSERT INTO error_logs
                (source, tool_name, error_type, error_message,
                 stack_trace, request_data, conversation_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    source,
                    tool_name,
                    error_type,
                    error_message,
                    stack_trace,
                    json.dumps(request_data) if request_data else None,
                    conversation_id,
                ),
            )
            storage.conn.commit()
    except Exception as e:
        logger.error(f"Failed to log error to DB: {e}")


def raise_http_error(
    status_code: int,
    detail: str,
    source: str = "api",
    tool_name: str = None,
    request_data: Dict[str, Any] = None,
) -> None:
    """Log error to DB and raise HTTPException."""
    log_error_to_db(
        source=source,
        tool_name=tool_name,
        error_type=f"HTTPException_{status_code}",
        error_message=detail,
        request_data=request_data,
    )
    raise HTTPException(status_code=status_code, detail=detail)


def normalize_strategy_parameters(params: Dict[str, Any], strategy_class: Type) -> Dict[str, Any]:
    """
    Normalize and filter strategy parameters.

    1. Apply parameter name aliases
    2. Filter out parameters not accepted by the strategy class (with logging)

    Returns filtered parameters that the strategy can accept.
    """
    if not params:
        return {}

    # Step 1: Apply aliases
    normalized = {}
    for key, value in params.items():
        canonical_key = PARAMETER_ALIASES.get(key, key)
        normalized[canonical_key] = value

    # Step 2: Get accepted parameters from strategy __init__
    sig = inspect.signature(strategy_class.__init__)
    accepted_params = {p.name for p in sig.parameters.values() if p.name != "self"}

    # Step 3: Filter and log what we're dropping
    filtered = {}
    dropped = []
    for key, value in normalized.items():
        if key in accepted_params:
            filtered[key] = value
        else:
            dropped.append(key)

    if dropped:
        logger.info(f"[{strategy_class.__name__}] Filtered out unsupported params: {dropped}")

    return filtered


# =============================================================================
# DEPRECATED: Old Pydantic models (use api.schemas instead)
# Kept for backward compatibility during migration
# =============================================================================

# NOTE: These models are deprecated. Import from api.schemas instead.
# Example: from api.schemas import DataFetchRequest
# The models below will be removed in a future version.


class DataFetchRequest_DEPRECATED(BaseModel):
    """DEPRECATED: Use api.schemas.DataFetchRequest instead"""

    symbol: str
    timeframe: str
    start_date: str  # ISO format: "2024-01-01"
    end_date: Optional[str] = None


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "running", "service": "Backtesting Research Tool API", "version": "1.0.0"}


@app.get("/api/data/stats")
def get_data_stats() -> list:
    """Get statistics about stored data in PostgreSQL"""
    try:
        with PostgresStorage(config["database"]) as storage:
            df = storage.get_data_stats()

            # Convert DataFrame to list of dicts
            stats = []
            for _, row in df.iterrows():
                stats.append(
                    {
                        "symbol": row["symbol"],
                        "timeframe": row["timeframe"],
                        "candle_count": int(row["candle_count"]),
                        "first_candle": row["first_candle"],
                        "last_candle": row["last_candle"],
                    }
                )

            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/api/data/fetch/stream")
async def fetch_data_stream(request: DataFetchRequest):
    """
    Streaming version of fetch_data that emits progress events via SSE.

    Events:
    - {"type": "progress", "pct": 0-100, "current": N, "total": M}
    - {"type": "done", "candles_fetched": N, "candles_inserted": M}
    - {"type": "error", "message": "..."}
    """

    async def event_generator():
        try:
            start_date = datetime.fromisoformat(request.start_date)
            end_date = datetime.fromisoformat(request.end_date) if request.end_date else None

            fetcher = BinanceBulkFetcher()
            final_df = None

            for event in fetcher.fetch_historical_with_progress(
                symbol=request.symbol,
                timeframe=request.timeframe,
                start_date=start_date,
                end_date=end_date,
            ):
                if event["type"] == "progress":
                    yield f"data: {json.dumps(event)}\n\n"
                elif event["type"] == "done":
                    final_df = event["df"]

            # Store in PostgreSQL
            inserted = 0
            if final_df is not None and not final_df.empty:
                with PostgresStorage(config["database"]) as storage:
                    storage.create_tables()
                    inserted = storage.insert_candles(final_df, request.symbol, request.timeframe)

            done_event = {
                "type": "done",
                "success": True,
                "candles_fetched": len(final_df) if final_df is not None else 0,
                "candles_inserted": inserted,
            }
            yield f"data: {json.dumps(done_event)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/data/fetch")
def fetch_data(request: DataFetchRequest) -> DataFetchResponse:
    """Fetch historical data from Binance and store in PostgreSQL"""
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date) if request.end_date else None

        # Fetch data
        fetcher = BinanceBulkFetcher()
        df = fetcher.fetch_historical(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return DataFetchResponse(
                success=False,
                message="No data fetched from Binance",
                candles_fetched=0,
                candles_inserted=0,
            )

        # Store in PostgreSQL
        with PostgresStorage(config["database"]) as storage:
            storage.create_tables()
            inserted = storage.insert_candles(df, request.symbol, request.timeframe)

        return DataFetchResponse(
            success=True,
            message=f"Successfully fetched and stored data for {request.symbol}",
            candles_fetched=len(df),
            candles_inserted=inserted,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@app.get("/api/data/range/{symbol}/{timeframe}")
def get_data_range(symbol: str, timeframe: str):
    """Get available data range for a symbol/timeframe"""
    try:
        with PostgresStorage(config["database"]) as storage:
            range_data = storage.get_available_data_range(symbol, timeframe)

            if range_data is None:
                return {"symbol": symbol, "timeframe": timeframe, "has_data": False}

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "has_data": True,
                "start_date": range_data[0],
                "end_date": range_data[1],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data range: {str(e)}")


@app.get("/api/data/candles/{symbol}/{timeframe}")
def get_candles(symbol: str, timeframe: str) -> list:
    """Get all candles for a symbol/timeframe for chart visualization"""
    try:
        with PostgresStorage(config["database"]) as storage:
            df = storage.get_candles(symbol, timeframe)

            if df.empty:
                raise HTTPException(
                    status_code=404, detail=f"No data found for {symbol} {timeframe}"
                )

            # Convert DataFrame to list of candle objects
            candles = []
            for _, row in df.iterrows():
                candles.append(
                    {
                        "time": int(row["open_time"].timestamp()),  # Convert to Unix timestamp
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    }
                )

            return candles
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get candles: {str(e)}")


@app.delete("/api/data/{symbol}/{timeframe}")
def delete_data(symbol: str, timeframe: str):
    """Delete all candles for a symbol/timeframe"""
    try:
        with PostgresStorage(config["database"]) as storage:
            deleted = storage.delete_candles(symbol, timeframe)

            if deleted == 0:
                raise HTTPException(
                    status_code=404, detail=f"No data found for {symbol} {timeframe}"
                )

            return {
                "success": True,
                "message": f"Deleted {deleted} candles for {symbol} {timeframe}",
                "deleted_count": deleted,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete data: {str(e)}")


@app.get("/api/data/regime/{symbol}/{timeframe}")
def get_regime_data(symbol: str, timeframe: str):
    """
    Get market regime data for visualization (HYBRID MODE)

    Strategy:
    1. Try to fetch pre-computed regimes from database (FAST: ~10ms)
    2. If not found, compute on-the-fly and optionally store (FALLBACK: ~61ms)

    Returns regime classification for each candle with:
    - Granular 3D regime (trend/volatility/momentum)
    - Simplified regime (TREND_UP/DOWN/RANGE/CHOPPY/NEUTRAL)
    - Confidence score (0.0-1.0)
    - Color for visualization
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            # HYBRID MODE: Try database first
            if storage.has_regimes(symbol, timeframe):
                # FAST PATH: Fetch pre-computed regimes (~10ms)
                regimes_df = storage.get_regimes(symbol, timeframe)

                # Map regimes to visualization colors
                regime_colors = {
                    "TREND_UP": "#22c55e",  # Green
                    "TREND_DOWN": "#ef4444",  # Red
                    "RANGE": "#3b82f6",  # Blue
                    "CHOPPY": "#f59e0b",  # Orange
                    "NEUTRAL": "#6b7280",  # Gray
                }

                # Format for frontend
                result = []
                for timestamp, row in regimes_df.iterrows():
                    simplified = row.get("simplified_regime")

                    result.append(
                        {
                            "time": int(timestamp.timestamp()),
                            "regime": simplified if not pd.isna(simplified) else "NEUTRAL",
                            "full_regime": row.get("full_regime", ""),
                            "trend_state": row.get("trend_state", ""),
                            "volatility_state": row.get("volatility_state", ""),
                            "momentum_state": row.get("momentum_state", ""),
                            "confidence": float(row.get("confidence", 0.5)),
                            "color": regime_colors.get(simplified, "#6b7280"),
                        }
                    )

                return result

            # FALLBACK: Compute on-the-fly (~61ms)
            # 1. Fetch candles from database
            df = storage.get_candles(symbol, timeframe)

            if df.empty:
                raise HTTPException(
                    status_code=404, detail=f"No data found for {symbol} {timeframe}"
                )

            # 2. Add all technical indicators
            df = add_all_indicators(df)

            # 3. Detect market regimes (event-driven, no lookahead)
            df = detect_market_regimes(df)

            # 4. Map regimes to visualization colors
            regime_colors = {
                "TREND_UP": "#22c55e",  # Green
                "TREND_DOWN": "#ef4444",  # Red
                "RANGE": "#3b82f6",  # Blue
                "CHOPPY": "#f59e0b",  # Orange
                "NEUTRAL": "#6b7280",  # Gray
            }

            # 5. Format for frontend
            result = []
            for _, row in df.iterrows():
                simplified = row.get("simplified_regime")

                result.append(
                    {
                        "time": int(row["open_time"].timestamp()),
                        "regime": simplified if not pd.isna(simplified) else "NEUTRAL",
                        "full_regime": row.get("full_regime", ""),
                        "trend_state": row.get("trend_state", ""),
                        "volatility_state": row.get("volatility_state", ""),
                        "momentum_state": row.get("momentum_state", ""),
                        "confidence": float(row.get("regime_confidence", 0.5)),
                        "color": regime_colors.get(simplified, "#6b7280"),
                    }
                )

            # Optional: Store computed regimes for next time (async)
            # Uncomment to enable auto-caching:
            # try:
            #     storage.insert_regimes(symbol, timeframe, df)
            # except Exception:
            #     pass  # Ignore storage errors

            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regimes: {str(e)}")


# =============================================================================
# STRATEGY ENDPOINTS
# =============================================================================


@app.get("/api/strategies", response_model=List[StrategyResponse])
def list_strategies():
    """
    List all available trading strategies.

    Returns strategies from the new 'strategies' table.
    Used by agent tool: list_strategies
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            query = """
                SELECT
                    name,
                    description,
                    class_name as strategy_type,
                    parameters,
                    regime_filter,
                    metadata
                FROM strategies
                ORDER BY created_at DESC
            """
            storage.cursor.execute(query)
            rows = storage.cursor.fetchall()

            return [
                StrategyResponse(
                    name=row[0],
                    description=row[1],
                    strategy_type=row[2],
                    parameters=row[3] or {},
                    regime_filter=row[4],
                    sub_regime_filter=None,  # Not used in new schema
                )
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@app.get("/api/strategies/{name:path}")
def get_strategy(name: str):
    """
    Get detailed information about a specific strategy.

    Used by agent tool: get_strategy
    """
    from urllib.parse import unquote

    name = unquote(name)  # Decode URL-encoded name
    try:
        with PostgresStorage(config["database"]) as storage:
            query = """
                SELECT
                    name,
                    description,
                    class_name,
                    parameters,
                    regime_filter,
                    metadata,
                    created_at,
                    updated_at
                FROM strategies
                WHERE name = %s
            """
            storage.cursor.execute(query, (name,))
            row = storage.cursor.fetchone()

            if not row:
                raise_http_error(
                    status_code=404,
                    detail=f"Strategy '{name}' not found",
                    tool_name="get_strategy",
                    request_data={"name": name},
                )

            return {
                "name": row[0],
                "description": row[1],
                "strategy_type": row[2],
                "builtin_class": row[2],  # class_name serves as builtin_class
                "parameters": row[3] or {},
                "entry_logic": None,  # Not used in new schema
                "exit_logic": None,  # Not used in new schema
                "regime_filter": row[4],
                "sub_regime_filter": None,  # Not used in new schema
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy: {str(e)}")


@app.post("/api/strategies")
def create_strategy(request: CreateStrategyRequest):
    """
    Create a new strategy (built-in variant or composite).

    Used by agent tool: create_strategy

    Built-in variant example:
        POST /api/strategies
        {
            "name": "MA Crossover 10/30 Fast",
            "description": "Faster MA crossover variant",
            "builtin_class": "MovingAverageCrossover",
            "parameters": {"fast_period": 10, "slow_period": 30},
            "regime_filter": ["TREND_UP", "TREND_DOWN"]
        }

    Composite strategy example:
        POST /api/strategies
        {
            "name": "My Composite Strategy",
            "description": "Custom logic-based strategy",
            "entry_logic": {...},
            "exit_logic": {...},
            "regime_filter": ["TREND_UP"]
        }
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            # Check for duplicate name
            check_query = "SELECT 1 FROM strategies WHERE name = %s"
            storage.cursor.execute(check_query, (request.name,))
            if storage.cursor.fetchone():
                raise_http_error(
                    status_code=400,
                    detail=f"Strategy '{request.name}' already exists",
                    tool_name="create_strategy",
                    request_data={"name": request.name},
                )

            # Determine strategy type and class name
            if request.builtin_class:
                # Built-in strategy variant
                strategy_type = "builtin"
                class_name = request.builtin_class
                builtin_class = request.builtin_class
                parameters = request.parameters or {}
                metadata = request.metadata or {
                    "category": "builtin-variant",
                    "preferred_regimes": request.regime_filter or [],
                    "risk_level": "moderate",
                }
            else:
                # Composite strategy
                strategy_type = "composite"
                class_name = "CompositeStrategy"
                builtin_class = None
                # Store entry/exit logic in parameters
                parameters = {
                    "entry_logic": request.entry_logic,
                    "exit_logic": request.exit_logic,
                    **(request.parameters or {}),
                }
                metadata = request.metadata or {
                    "category": "composite",
                    "preferred_regimes": request.regime_filter or [],
                    "risk_level": "moderate",
                }

            # Insert into strategies table
            # Includes both old schema columns (strategy_type, builtin_class)
            # and new schema columns (class_name, metadata) for compatibility
            insert_query = """
                INSERT INTO strategies
                (name, class_name, description, metadata, parameters, regime_filter,
                 strategy_type, builtin_class, entry_logic, exit_logic)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, class_name
            """

            storage.cursor.execute(
                insert_query,
                (
                    request.name,
                    class_name,
                    request.description,
                    json.dumps(metadata),
                    json.dumps(parameters),
                    request.regime_filter if request.regime_filter else None,
                    strategy_type,
                    builtin_class,
                    json.dumps(request.entry_logic) if request.entry_logic else None,
                    json.dumps(request.exit_logic) if request.exit_logic else None,
                ),
            )

            result = storage.cursor.fetchone()
            storage.conn.commit()

            return {
                "success": True,
                "strategy": {"id": result[0], "name": result[1], "class_name": result[2]},
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create strategy: {str(e)}")


@app.delete("/api/strategies/{name:path}")
def delete_strategy(name: str):
    """Delete a strategy from strategies table"""
    from urllib.parse import unquote

    name = unquote(name)  # Decode URL-encoded name
    try:
        with PostgresStorage(config["database"]) as storage:
            query = "DELETE FROM strategies WHERE name = %s RETURNING id"
            storage.cursor.execute(query, (name,))
            result = storage.cursor.fetchone()
            storage.conn.commit()

            if not result:
                raise_http_error(
                    status_code=404,
                    detail=f"Strategy '{name}' not found",
                    tool_name="delete_strategy",
                    request_data={"name": name},
                )

            return {"success": True, "message": f"Strategy '{name}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete strategy: {str(e)}")


# =============================================================================
# BACKTEST ENDPOINT
# =============================================================================


@app.post("/api/backtest", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest):
    """
    Run a backtest with specified strategy on historical data.

    Domain model: Backtest = f(Strategy, Dataset)
    - Strategy must exist in database
    - Dataset (candles) must exist for the requested range

    Used by agent tool: run_backtest

    Returns metrics and trade data for AI analysis.
    """
    try:
        # 1. Get strategy from database (new strategies table)
        with PostgresStorage(config["database"]) as storage:
            query = """
                SELECT name, class_name, parameters, regime_filter
                FROM strategies
                WHERE name = %s
            """
            storage.cursor.execute(query, (request.strategy_name,))
            row = storage.cursor.fetchone()

            if not row:
                raise_http_error(
                    status_code=404,
                    detail=(
                        f"Strategy '{request.strategy_name}' not found."
                        " Use list_strategies to see available strategies."
                    ),
                    tool_name="run_backtest",
                    request_data=request.model_dump(),
                )

            strategy_name, class_name, parameters, regime_filter = row

        # 2. Check if data exists
        with PostgresStorage(config["database"]) as data_storage:
            # Parse dates
            start_dt = datetime.fromisoformat(request.start_date)
            end_dt = datetime.fromisoformat(request.end_date) if request.end_date else None

            # Check data availability
            data_range = data_storage.get_available_data_range(request.symbol, request.timeframe)
            if data_range is None:
                raise_http_error(
                    status_code=404,
                    detail=(
                        f"No data found for {request.symbol}"
                        f" {request.timeframe}. Fetch data first"
                        " using /api/data/fetch."
                    ),
                    tool_name="run_backtest",
                    request_data=request.model_dump(),
                )

            # Get candles
            df = data_storage.get_candles(
                request.symbol, request.timeframe, start_time=start_dt, end_time=end_dt
            )

            if df.empty:
                raise_http_error(
                    status_code=400,
                    detail=(
                        f"No candles found for {request.symbol}"
                        f" {request.timeframe} in range"
                        f" {request.start_date} to {request.end_date}"
                    ),
                    tool_name="run_backtest",
                    request_data=request.model_dump(),
                )

        # 3. Merge parameters (database params + override params)
        final_params = {**(parameters or {}), **(request.parameters or {})}

        # Apply regime filter override if provided
        final_regime_filter = request.regime_filter if request.regime_filter else regime_filter

        # 4. Instantiate strategy from class name
        from core.backtest.strategies import (
            BollingerBands,
            MACDCross,
            MovingAverageCrossover,
            RSIReversal,
        )

        # Map class names to actual classes
        STRATEGY_CLASSES = {
            "MovingAverageCrossover": MovingAverageCrossover,
            "RSIReversal": RSIReversal,
            "MACDCross": MACDCross,
            "BollingerBands": BollingerBands,
        }

        strategy_class = STRATEGY_CLASSES.get(class_name)
        if not strategy_class:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown strategy class: {class_name}."
                    f" Available: {list(STRATEGY_CLASSES.keys())}"
                ),
            )

        # Normalize and filter parameters to match strategy's __init__ signature
        validated_params = normalize_strategy_parameters(final_params, strategy_class)
        strategy = strategy_class(**validated_params)

        # Apply regime filter if provided
        if hasattr(strategy, "regime_filter") and final_regime_filter:
            strategy.regime_filter = final_regime_filter

        # 5. Run backtest
        from core.backtest import BacktestEngine

        engine = BacktestEngine(
            data=df,
            strategy=strategy,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate,
            position_size_pct=request.position_size_pct,
            enable_regime_detection=True,
        )

        results = engine.run()

        # 6. Get regime stats if available
        regime_stats = None
        if hasattr(strategy, "get_regime_stats"):
            regime_stats = strategy.get_regime_stats()

        # 7. Format response data
        # Get actual date range from data
        actual_start = df.index[0] if hasattr(df.index[0], "isoformat") else df.iloc[0]["open_time"]
        actual_end = (
            df.index[-1] if hasattr(df.index[-1], "isoformat") else df.iloc[-1]["open_time"]
        )

        start_date_str = (
            actual_start.isoformat() if hasattr(actual_start, "isoformat") else str(actual_start)
        )
        end_date_str = (
            actual_end.isoformat() if hasattr(actual_end, "isoformat") else str(actual_end)
        )

        # Format metrics
        total_return_pct = round(results["metrics"].get("total_return", 0), 4)
        sharpe_ratio = round(results["metrics"].get("sharpe_ratio", 0), 4)
        max_drawdown_pct = round(results["metrics"].get("max_drawdown", 0), 4)
        win_rate_pct = round(results["metrics"].get("win_rate", 0), 2)
        total_trades = results["metrics"].get("total_trades", 0)
        profit_factor = round(results["metrics"].get("profit_factor", 0), 4)

        # Format equity curve
        equity_curve = [
            {
                "time": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                "value": round(val, 2),
            }
            for ts, val in results["equity_curve"]
        ]

        # Format trades
        trades_list = [
            TradeResult(
                entry_time=(
                    t.entry_time.isoformat()
                    if hasattr(t.entry_time, "isoformat")
                    else str(t.entry_time)
                ),
                exit_time=(
                    t.exit_time.isoformat()
                    if hasattr(t.exit_time, "isoformat")
                    else str(t.exit_time)
                ),
                entry_price=round(t.entry_price, 2),
                exit_price=round(t.exit_price, 2),
                pnl=round(t.pnl, 2),
                pnl_pct=round(t.return_pct, 4),
                duration_hours=(
                    round(t.duration.total_seconds() / 3600, 2)
                    if hasattr(t.duration, "total_seconds")
                    else 0
                ),
            )
            for t in results["trades"]
        ]

        # 8. Auto-save report to database
        report_id = None
        try:
            with PostgresStorage(config["database"]) as storage:
                # Check which columns exist in backtest_reports
                storage.cursor.execute(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'backtest_reports'
                """
                )
                existing_cols = {row[0] for row in storage.cursor.fetchall()}

                # Define all desired columns and their values
                desired = [
                    ("strategy_name", request.strategy_name),
                    ("strategy_config", json.dumps(final_params)),
                    ("symbol", request.symbol),
                    ("timeframe", request.timeframe),
                    ("start_date", start_date_str[:10]),
                    ("end_date", end_date_str[:10]),
                    ("initial_capital", request.initial_capital),
                    ("total_return_pct", total_return_pct),
                    ("sharpe_ratio", sharpe_ratio),
                    ("max_drawdown_pct", max_drawdown_pct),
                    ("win_rate_pct", win_rate_pct),
                    ("total_trades", total_trades),
                    ("profit_factor", profit_factor),
                    ("equity_curve", json.dumps(equity_curve)),
                    ("trades", json.dumps([t.model_dump() for t in trades_list])),
                    ("regime_performance", json.dumps(regime_stats) if regime_stats else None),
                ]

                # Only insert columns that exist in the table
                filtered = [(c, v) for c, v in desired if c in existing_cols]
                columns = [c for c, v in filtered]
                values = [v for c, v in filtered]

                placeholders = ", ".join(["%s"] * len(columns))
                col_names = ", ".join(columns)
                query = f"""
                    INSERT INTO backtest_reports ({col_names})
                    VALUES ({placeholders})
                    RETURNING id
                """  # nosec B608 - column names from hardcoded list

                storage.cursor.execute(query, values)

                result = storage.cursor.fetchone()
                storage.conn.commit()
                report_id = str(result[0])
        except Exception as save_err:
            # Log but don't fail the backtest if saving fails
            print(f"Warning: Failed to auto-save report: {save_err}")

        # 9. Return response
        return BacktestResponse(
            success=True,
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=start_date_str,
            end_date=end_date_str,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            win_rate_pct=win_rate_pct,
            total_trades=total_trades,
            profit_factor=profit_factor,
            equity_curve=equity_curve,
            trades=trades_list,
            regime_stats=regime_stats,
            report_id=report_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Backtest failed: {e}\n{tb}")

        # Log to database for later analysis
        log_error_to_db(
            source="api",
            tool_name="run_backtest",
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=tb,
            request_data=request.model_dump(),
        )

        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.get("/api/data/check/{symbol}/{timeframe}")
def check_data_availability(
    symbol: str, timeframe: str, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    """
    Check if data is available for backtesting.

    Used by agent to validate before running backtest.
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            data_range = storage.get_available_data_range(symbol, timeframe)

            if data_range is None:
                return {
                    "available": False,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "message": "No data found. Use /api/data/fetch to download data.",
                }

            # Check if requested range is covered
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                if start_dt < data_range[0]:
                    return {
                        "available": False,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "data_start": data_range[0].isoformat(),
                        "data_end": data_range[1].isoformat(),
                        "message": (
                            f"Requested start date {start_date}"
                            " is before available data"
                            f" ({data_range[0].date()})"
                        ),
                    }

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                if end_dt > data_range[1]:
                    return {
                        "available": False,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "data_start": data_range[0].isoformat(),
                        "data_end": data_range[1].isoformat(),
                        "message": (
                            f"Requested end date {end_date}"
                            " is after available data"
                            f" ({data_range[1].date()})"
                        ),
                    }

            return {
                "available": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data_start": data_range[0].isoformat(),
                "data_end": data_range[1].isoformat(),
                "message": "Data is available for the requested range",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check data: {str(e)}")


# =============================================================================
# AGENT ENDPOINTS
# =============================================================================


def create_research_event_from_tool(project_id: str, tool_name: str, tool_result: dict):
    """
    Create a research event in the timeline based on a successful tool call.
    Returns the created event or None if no event should be created.
    """
    if not project_id:
        return None

    # Map tool names to event types and titles
    event_mappings = {
        "create_strategy": {
            "event_type": "strategy_created",
            "title_template": "Created strategy: {name}",
            "summary_template": "{description}" if "{description}" else None,
            "reference_type": "strategy",
        },
        "run_backtest": {
            "event_type": "backtest_run",
            "title_template": "Backtest: {strategy_name} on {symbol}",
            "summary_template": (
                "Return: {total_return_pct:.1f}%,"
                " Sharpe: {sharpe_ratio:.2f},"
                " Trades: {total_trades}"
            ),
            "reference_type": "backtest_report",
        },
    }

    if tool_name not in event_mappings or not tool_result:
        return None

    # Check for errors
    if tool_result.get("error"):
        return None

    mapping = event_mappings[tool_name]

    try:
        # Build title from template
        title = mapping["title_template"].format(**tool_result)

        # Build summary from template if data available
        summary = None
        if mapping.get("summary_template"):
            try:
                # For backtest, metrics might be nested
                if tool_name == "run_backtest" and "metrics" in tool_result:
                    metrics = tool_result["metrics"]
                    summary = (
                        f"Return: {metrics.get('total_return_pct', 0):.1f}%,"
                        f" Sharpe: {metrics.get('sharpe_ratio', 0):.2f},"
                        f" Trades: {metrics.get('total_trades', 0)}"
                    )
                else:
                    summary = mapping["summary_template"].format(**tool_result)
            except (KeyError, TypeError):
                pass

        # Get reference_id
        reference_id = None
        if tool_name == "create_strategy":
            reference_id = tool_result.get("name")
        elif tool_name == "run_backtest":
            reference_id = tool_result.get("report_id")

        # Create event in database
        with PostgresStorage(config["database"]) as storage:
            from uuid import uuid4

            event_id = str(uuid4())
            query = """
                INSERT INTO research_events
                    (id, project_id, event_type, title,
                     summary, reference_type, reference_id,
                     data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            storage.cursor.execute(
                query,
                (
                    event_id,
                    project_id,
                    mapping["event_type"],
                    title[:200],  # Limit title length
                    summary[:500] if summary else None,  # Limit summary length
                    mapping["reference_type"],
                    reference_id,
                    json.dumps(tool_result, default=str),
                ),
            )
            storage.conn.commit()
            return event_id

    except Exception as e:
        print(f"Failed to create research event: {e}")
        return None


@app.post("/api/agent/chat")
async def agent_chat(request: AgentChatRequest):
    """
    Chat with the backtesting research agent.

    The agent can:
    - Help design trading strategies
    - Run backtests
    - Analyze results
    - Provide recommendations

    Returns structured response with message, phase, and metadata.
    """
    try:
        from uuid import UUID

        from agent import create_agent

        agent = create_agent()

        conv_id = UUID(request.conversation_id) if request.conversation_id else None
        response = await agent.chat(request.message, conv_id)

        return {
            "message": response.message,
            "conversation_id": str(response.conversation_id),
            "phase": response.phase.value,
            "awaiting_confirmation": response.awaiting_confirmation,
            "confirmation_prompt": response.confirmation_prompt,
            "data": response.data,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "timestamp": tc.timestamp.isoformat(),
                }
                for tc in response.tool_calls
            ],
            "tokens_used": response.tokens_used,
            "cost_usd": response.cost_usd,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.post("/api/agent/chat/stream")
async def agent_chat_stream(request: AgentChatRequest):
    """
    Chat with the backtesting research agent using Server-Sent Events (SSE).

    Streams events as they happen:
    - text_delta: Partial text as it's generated
    - tool_start: When agent starts using a tool
    - tool_result: When tool execution completes
    - done: Final metadata (conversation_id, tokens, cost)
    - error: If something goes wrong

    This provides real-time visibility into agent's progress.
    """
    from uuid import UUID

    from agent import create_agent

    agent = create_agent()
    conv_id = UUID(request.conversation_id) if request.conversation_id else None
    project_id = request.project_id
    proj_uuid = UUID(project_id) if project_id else None

    async def event_generator():
        try:
            async for event in agent.chat_stream(request.message, conv_id, project_id=proj_uuid):
                # Intercept tool_result events to create timeline events
                if event.get("type") == "tool_result":
                    tool_name = event.get("tool")
                    tool_result = event.get("result")
                    is_success = event.get("success", False)
                    print(
                        f"[DEBUG] tool_result: tool={tool_name},"
                        f" success={is_success},"
                        f" project_id={project_id}"
                    )

                    if project_id and is_success and tool_name and tool_result:
                        event_id = create_research_event_from_tool(
                            project_id, tool_name, tool_result
                        )
                        print(f"[DEBUG] Created research event: {event_id}")

                # Format as SSE
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            import traceback

            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# =============================================================================
# CONVERSATION ENDPOINTS
# =============================================================================


@app.get("/api/projects/{project_id}/conversations")
async def list_project_conversations(project_id: str, limit: int = 50):
    """List conversations for a project."""
    from agent.core import ConversationStorage

    storage = ConversationStorage()
    return await storage.list_by_project(project_id, limit)


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get full conversation with messages."""
    from agent.core import ConversationStorage

    storage = ConversationStorage()
    result = await storage.get_full(conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


# =============================================================================
# REPORTS ENDPOINTS
# =============================================================================


@app.get("/api/reports")
def list_reports(limit: int = 50):
    """List saved backtest reports."""
    try:
        with PostgresStorage(config["database"]) as storage:
            query = """
                SELECT
                    id, strategy_name, symbol, timeframe,
                    start_date, end_date, total_return_pct,
                    sharpe_ratio, total_trades, created_at
                FROM backtest_reports
                ORDER BY created_at DESC
                LIMIT %s
            """
            storage.cursor.execute(query, (limit,))
            rows = storage.cursor.fetchall()

            return [
                {
                    "id": str(row[0]),
                    "strategy_name": row[1],
                    "symbol": row[2],
                    "timeframe": row[3],
                    "start_date": row[4].isoformat() if row[4] else None,
                    "end_date": row[5].isoformat() if row[5] else None,
                    "total_return_pct": float(row[6]) if row[6] else None,
                    "sharpe_ratio": float(row[7]) if row[7] else None,
                    "total_trades": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    """Get full backtest report by ID."""
    try:
        from uuid import UUID

        # Validate UUID format
        UUID(report_id)

        with PostgresStorage(config["database"]) as storage:
            query = """
                SELECT *
                FROM backtest_reports
                WHERE id = %s
            """
            storage.cursor.execute(query, (report_id,))
            row = storage.cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

            # Get column names
            columns = [desc[0] for desc in storage.cursor.description]
            report = dict(zip(columns, row))

            # Convert UUID and datetime fields
            report["id"] = str(report["id"])
            if report.get("conversation_id"):
                report["conversation_id"] = str(report["conversation_id"])
            if report.get("created_at"):
                report["created_at"] = report["created_at"].isoformat()

            # Convert decimal fields to float
            decimal_fields = [
                "initial_capital",
                "total_return_pct",
                "sharpe_ratio",
                "max_drawdown_pct",
                "win_rate_pct",
                "profit_factor",
                "calmar_ratio",
                "sortino_ratio",
                "recovery_factor",
                "avg_trade_duration_hours",
                "best_trade_pct",
                "worst_trade_pct",
            ]
            for field in decimal_fields:
                if report.get(field) is not None:
                    report[field] = float(report[field])

            return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@app.post("/api/reports")
def save_report(request: dict):
    """
    Save backtest results as a persistent report.

    Used by agent tool: save_report
    """
    try:
        backtest_results = request.get("backtest_results", {})
        ai_summary = request.get("ai_summary")
        ai_recommendations = request.get("ai_recommendations", [])
        ai_concerns = request.get("ai_concerns", [])

        with PostgresStorage(config["database"]) as storage:
            # Check which columns exist in backtest_reports
            storage.cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'backtest_reports'
            """
            )
            existing_columns = {row[0] for row in storage.cursor.fetchall()}

            # Define all desired columns and their values
            desired = [
                ("strategy_name", backtest_results.get("strategy_name")),
                ("strategy_config", json.dumps(backtest_results.get("strategy_config", {}))),
                ("symbol", backtest_results.get("symbol")),
                ("timeframe", backtest_results.get("timeframe")),
                ("start_date", backtest_results.get("start_date")),
                ("end_date", backtest_results.get("end_date")),
                ("initial_capital", backtest_results.get("initial_capital", 10000)),
                ("total_return_pct", backtest_results.get("total_return_pct")),
                ("sharpe_ratio", backtest_results.get("sharpe_ratio")),
                ("max_drawdown_pct", backtest_results.get("max_drawdown_pct")),
                ("win_rate_pct", backtest_results.get("win_rate_pct")),
                ("total_trades", backtest_results.get("total_trades")),
                ("profit_factor", backtest_results.get("profit_factor")),
                ("equity_curve", json.dumps(backtest_results.get("equity_curve", []))),
                ("trades", json.dumps(backtest_results.get("trades", []))),
                ("ai_summary", ai_summary),
                ("ai_recommendations", json.dumps(ai_recommendations)),
                ("ai_concerns", json.dumps(ai_concerns)),
            ]

            # Only insert columns that exist in the table
            filtered = [(c, v) for c, v in desired if c in existing_columns]
            columns = [c for c, v in filtered]
            values = [v for c, v in filtered]

            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join(columns)
            query = f"""
                INSERT INTO backtest_reports ({col_names})
                VALUES ({placeholders})
                RETURNING id
            """  # nosec B608 - column names from hardcoded list

            storage.cursor.execute(query, values)
            result = storage.cursor.fetchone()
            storage.conn.commit()

            return {"success": True, "report_id": str(result[0])}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")


# =============================================================================
# SUGGESTIONS ENDPOINT
# =============================================================================


@app.post("/api/suggestions")
def save_suggestion(request: dict):
    """
    Save an agent suggestion for tool improvement.

    Used by agent tool: suggest_enhancement
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            # Validate conversation_id FK if provided
            conversation_id = request.get("conversation_id")
            if conversation_id:
                storage.cursor.execute(
                    "SELECT 1 FROM conversations WHERE id = %s",
                    (conversation_id,),
                )
                if not storage.cursor.fetchone():
                    conversation_id = None  # Skip invalid FK

            query = """
                INSERT INTO agent_suggestions (
                    category, title, description, rationale,
                    conversation_id
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """

            storage.cursor.execute(
                query,
                (
                    request.get("category"),
                    request.get("title"),
                    request.get("description"),
                    request.get("rationale"),
                    conversation_id,
                ),
            )

            result = storage.cursor.fetchone()
            storage.conn.commit()

            return {"success": True, "suggestion_id": str(result[0])}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save suggestion: {str(e)}")


@app.get("/api/suggestions")
def list_suggestions(status: Optional[str] = None, limit: int = 50):
    """List agent suggestions for tool improvements."""
    try:
        with PostgresStorage(config["database"]) as storage:
            if status:
                query = """
                    SELECT id, category, title, description, rationale, status, created_at
                    FROM agent_suggestions
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                storage.cursor.execute(query, (status, limit))
            else:
                query = """
                    SELECT id, category, title, description, rationale, status, created_at
                    FROM agent_suggestions
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                storage.cursor.execute(query, (limit,))

            rows = storage.cursor.fetchall()

            return [
                {
                    "id": str(row[0]),
                    "category": row[1],
                    "title": row[2],
                    "description": row[3],
                    "rationale": row[4],
                    "status": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list suggestions: {str(e)}")


# =============================================================================
# ERROR LOGS ENDPOINTS
# =============================================================================


@app.get("/api/errors")
def list_error_logs(limit: int = 50, source: Optional[str] = None, tool_name: Optional[str] = None):
    """
    List recent error logs for debugging.

    Query params:
    - limit: Max number of errors to return (default: 50)
    - source: Filter by source ('api', 'mcp_tool', 'agent', 'backtest')
    - tool_name: Filter by specific tool name
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            conditions: list = []
            params: list = []

            if source:
                conditions.append("source = %s")
                params.append(source)
            if tool_name:
                conditions.append("tool_name = %s")
                params.append(tool_name)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT id, source, tool_name, error_type,
                       error_message, request_data,
                       created_at, resolved_at
                FROM error_logs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """  # nosec B608
            params.append(limit)

            storage.cursor.execute(query, params)
            rows = storage.cursor.fetchall()

            return [
                {
                    "id": str(row[0]),
                    "source": row[1],
                    "tool_name": row[2],
                    "error_type": row[3],
                    "error_message": row[4],
                    "request_data": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "resolved_at": row[7].isoformat() if row[7] else None,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list errors: {str(e)}")


@app.post("/api/errors")
def log_error(request: LogErrorRequest):
    """
    Log an error from external sources (e.g., MCP server).

    This endpoint allows the MCP server to log errors to the database
    when it encounters connection issues or other errors.
    """
    try:
        log_error_to_db(
            source=request.source,
            tool_name=request.tool_name,
            error_type=request.error_type,
            error_message=request.error_message,
            stack_trace=request.stack_trace,
            request_data=request.request_data,
            conversation_id=request.conversation_id,
        )
        return {"success": True, "message": "Error logged successfully"}
    except Exception as e:
        # Don't fail if logging fails - just return error
        return {"success": False, "message": f"Failed to log error: {str(e)}"}


@app.get("/api/errors/{error_id}")
def get_error_log(error_id: str):
    """Get full error details including stack trace."""
    try:
        with PostgresStorage(config["database"]) as storage:
            storage.cursor.execute(
                """
                SELECT id, source, tool_name, error_type, error_message,
                       stack_trace, request_data, conversation_id,
                       created_at, resolved_at, resolution_notes
                FROM error_logs
                WHERE id = %s
            """,
                (error_id,),
            )

            row = storage.cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Error log not found")

            return {
                "id": str(row[0]),
                "source": row[1],
                "tool_name": row[2],
                "error_type": row[3],
                "error_message": row[4],
                "stack_trace": row[5],
                "request_data": row[6],
                "conversation_id": str(row[7]) if row[7] else None,
                "created_at": row[8].isoformat() if row[8] else None,
                "resolved_at": row[9].isoformat() if row[9] else None,
                "resolution_notes": row[10],
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error: {str(e)}")


@app.patch("/api/errors/{error_id}/resolve")
def resolve_error(error_id: str, resolution_notes: str = None):
    """Mark an error as resolved with optional notes."""
    try:
        with PostgresStorage(config["database"]) as storage:
            storage.cursor.execute(
                """
                UPDATE error_logs
                SET resolved_at = NOW(), resolution_notes = %s
                WHERE id = %s
                RETURNING id
            """,
                (resolution_notes, error_id),
            )

            result = storage.cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Error log not found")

            storage.conn.commit()
            return {"success": True, "resolved_id": str(result[0])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve error: {str(e)}")


# =============================================================================
# PROJECTS ENDPOINTS
# =============================================================================


@app.get("/api/projects")
def list_projects(status: Optional[str] = None, limit: int = 50):
    """
    List all projects.

    Query params:
    - status: Filter by status (active, paused, concluded)
    - limit: Max number of projects to return
    """
    try:
        with PostgresStorage(config["database"]) as storage:
            if status:
                query = """
                    SELECT p.id, p.name, p.description, p.thesis, p.status, p.validation_result,
                           COALESCE(c.conv_count, 0) AS conversation_count,
                           COALESCE(b.bt_count, 0) AS backtest_count,
                           p.created_at, p.updated_at
                    FROM projects p
                    LEFT JOIN (
                        SELECT project_id, COUNT(*) AS conv_count
                        FROM conversations
                        GROUP BY project_id
                    ) c ON c.project_id = p.id
                    LEFT JOIN (
                        SELECT project_id, COUNT(*) AS bt_count
                        FROM research_events
                        WHERE event_type = 'backtest_run'
                        GROUP BY project_id
                    ) b ON b.project_id = p.id
                    WHERE p.status = %s
                    ORDER BY p.updated_at DESC
                    LIMIT %s
                """
                storage.cursor.execute(query, (status, limit))
            else:
                query = """
                    SELECT p.id, p.name, p.description, p.thesis, p.status, p.validation_result,
                           COALESCE(c.conv_count, 0) AS conversation_count,
                           COALESCE(b.bt_count, 0) AS backtest_count,
                           p.created_at, p.updated_at
                    FROM projects p
                    LEFT JOIN (
                        SELECT project_id, COUNT(*) AS conv_count
                        FROM conversations
                        GROUP BY project_id
                    ) c ON c.project_id = p.id
                    LEFT JOIN (
                        SELECT project_id, COUNT(*) AS bt_count
                        FROM research_events
                        WHERE event_type = 'backtest_run'
                        GROUP BY project_id
                    ) b ON b.project_id = p.id
                    ORDER BY p.updated_at DESC
                    LIMIT %s
                """
                storage.cursor.execute(query, (limit,))

            rows = storage.cursor.fetchall()

            return [
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "thesis": row[3],
                    "status": row[4],
                    "validation_result": row[5],
                    "conversation_count": row[6],
                    "backtest_count": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "updated_at": row[9].isoformat() if row[9] else None,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@app.post("/api/projects")
def create_project(request: CreateProjectRequest):
    """Create a new project."""
    try:
        with PostgresStorage(config["database"]) as storage:
            query = """
                INSERT INTO projects (name, description, thesis, user_preferences)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, created_at
            """
            storage.cursor.execute(
                query,
                (
                    request.name,
                    request.description,
                    request.thesis,
                    json.dumps(request.user_preferences) if request.user_preferences else "{}",
                ),
            )

            result = storage.cursor.fetchone()
            storage.conn.commit()

            return {
                "success": True,
                "project": {
                    "id": str(result[0]),
                    "name": result[1],
                    "created_at": result[2].isoformat() if result[2] else None,
                },
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    """Get project details by ID."""
    try:
        from uuid import UUID

        UUID(project_id)  # Validate UUID format

        with PostgresStorage(config["database"]) as storage:
            query = """
                SELECT p.id, p.name, p.description, p.thesis, p.status, p.validation_result,
                       p.user_preferences, p.notebook,
                       COALESCE(c.conv_count, 0) AS conversation_count,
                       COALESCE(b.bt_count, 0) AS backtest_count,
                       p.created_at, p.updated_at
                FROM projects p
                LEFT JOIN (
                    SELECT project_id, COUNT(*) AS conv_count
                    FROM conversations
                    WHERE project_id = %s
                    GROUP BY project_id
                ) c ON c.project_id = p.id
                LEFT JOIN (
                    SELECT project_id, COUNT(*) AS bt_count
                    FROM research_events
                    WHERE project_id = %s AND event_type = 'backtest_run'
                    GROUP BY project_id
                ) b ON b.project_id = p.id
                WHERE p.id = %s
            """
            storage.cursor.execute(query, (project_id, project_id, project_id))
            row = storage.cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

            return {
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "thesis": row[3],
                "status": row[4],
                "validation_result": row[5],
                "user_preferences": row[6],
                "notebook": row[7] or [],
                "conversation_count": row[8],
                "backtest_count": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")


@app.patch("/api/projects/{project_id}")
def update_project(project_id: str, request: UpdateProjectRequest):
    """Update project details."""
    try:
        from uuid import UUID

        UUID(project_id)  # Validate UUID format

        # Build dynamic update query
        updates = []
        params = []

        if request.name is not None:
            updates.append("name = %s")
            params.append(request.name)
        if request.description is not None:
            updates.append("description = %s")
            params.append(request.description)
        if request.thesis is not None:
            updates.append("thesis = %s")
            params.append(request.thesis)
        if request.status is not None:
            updates.append("status = %s")
            params.append(request.status)
        if request.validation_result is not None:
            updates.append("validation_result = %s")
            params.append(request.validation_result)
        if request.notebook is not None:
            updates.append("notebook = %s")
            params.append(json.dumps(request.notebook))

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(project_id)

        with PostgresStorage(config["database"]) as storage:
            query = f"""
                UPDATE projects
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, name, updated_at
            """  # nosec B608
            storage.cursor.execute(query, params)
            result = storage.cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

            storage.conn.commit()

            return {
                "success": True,
                "project": {
                    "id": str(result[0]),
                    "name": result[1],
                    "updated_at": result[2].isoformat() if result[2] else None,
                },
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@app.post("/api/projects/{project_id}/notebook/blocks")
def add_notebook_block(project_id: str, block: dict):
    """
    Append a block to the project notebook.

    Block types: text, backtest_ref, strategy_ref, agent_note
    Used by agent to add insights and artifact references.
    """
    try:
        from uuid import UUID, uuid4

        UUID(project_id)

        # Validate block has required fields
        block_type = block.get("type")
        if block_type not in ("text", "backtest_ref", "strategy_ref", "agent_note"):
            raise HTTPException(status_code=400, detail=f"Invalid block type: {block_type}")

        # Add metadata
        block["id"] = str(uuid4())
        block["created_at"] = datetime.now().isoformat()

        with PostgresStorage(config["database"]) as storage:
            query = """
                UPDATE projects
                SET notebook = COALESCE(notebook, '[]'::jsonb) || %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id
            """
            storage.cursor.execute(query, (json.dumps([block]), project_id))
            result = storage.cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

            storage.conn.commit()
            return {"success": True, "block": block}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add notebook block: {str(e)}")


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    """Delete a project and all its events."""
    try:
        from uuid import UUID

        UUID(project_id)  # Validate UUID format

        with PostgresStorage(config["database"]) as storage:
            # Events are deleted via CASCADE
            query = "DELETE FROM projects WHERE id = %s RETURNING id, name"
            storage.cursor.execute(query, (project_id,))
            result = storage.cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

            storage.conn.commit()

            return {"success": True, "message": f"Project '{result[1]}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


# =============================================================================
# RESEARCH EVENTS ENDPOINTS
# =============================================================================


@app.get("/api/projects/{project_id}/events")
def list_project_events(project_id: str, event_type: Optional[str] = None, limit: int = 100):
    """
    List research events for a project (timeline data).

    Query params:
    - event_type: Filter by type (strategy_created, backtest_run, conclusion, note, milestone)
    - limit: Max number of events to return
    """
    try:
        from uuid import UUID

        UUID(project_id)  # Validate UUID format

        with PostgresStorage(config["database"]) as storage:
            if event_type:
                query = """
                    SELECT id, event_type, title, summary, reference_type, reference_id,
                           data, created_at
                    FROM research_events
                    WHERE project_id = %s AND event_type = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                storage.cursor.execute(query, (project_id, event_type, limit))
            else:
                query = """
                    SELECT id, event_type, title, summary, reference_type, reference_id,
                           data, created_at
                    FROM research_events
                    WHERE project_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                storage.cursor.execute(query, (project_id, limit))

            rows = storage.cursor.fetchall()

            return [
                {
                    "id": str(row[0]),
                    "event_type": row[1],
                    "title": row[2],
                    "summary": row[3],
                    "reference_type": row[4],
                    "reference_id": str(row[5]) if row[5] else None,
                    "data": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")


@app.post("/api/projects/{project_id}/events")
def create_project_event(project_id: str, request: CreateEventRequest):
    """Create a new research event for a project."""
    try:
        from uuid import UUID

        UUID(project_id)  # Validate UUID format

        with PostgresStorage(config["database"]) as storage:
            # Check project exists
            storage.cursor.execute("SELECT 1 FROM projects WHERE id = %s", (project_id,))
            if not storage.cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

            query = """
                INSERT INTO research_events
                (project_id, event_type, title, summary, reference_type, reference_id, data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """
            storage.cursor.execute(
                query,
                (
                    project_id,
                    request.event_type,
                    request.title,
                    request.summary,
                    request.reference_type,
                    request.reference_id,
                    json.dumps(request.data) if request.data else "{}",
                ),
            )

            result = storage.cursor.fetchone()
            storage.conn.commit()

            return {
                "success": True,
                "event": {
                    "id": str(result[0]),
                    "created_at": result[1].isoformat() if result[1] else None,
                },
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


# =============================================================================
# ONBOARDING PREFERENCES ENDPOINT
# =============================================================================


@app.post("/api/onboarding/preferences")
def save_onboarding_preferences(request: OnboardingPreferencesRequest):
    """
    Save onboarding preferences and optionally create first project.

    Returns project ID if first project was created.
    """
    try:
        preferences = {
            "experience_level": request.experience_level,
            "goals": request.goals,
            "onboarding_completed_at": datetime.now().isoformat(),
        }

        project_id = None

        # Create first project if name provided
        if request.first_project_name:
            with PostgresStorage(config["database"]) as storage:
                query = """
                    INSERT INTO projects (name, thesis, user_preferences)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """
                storage.cursor.execute(
                    query,
                    (
                        request.first_project_name,
                        request.first_project_thesis,
                        json.dumps(preferences),
                    ),
                )
                result = storage.cursor.fetchone()
                storage.conn.commit()
                project_id = str(result[0])

        return {"success": True, "preferences": preferences, "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save preferences: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
