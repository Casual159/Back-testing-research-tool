"""
FastAPI Backend for Backtesting Research Tool
Provides REST API endpoints for the Next.js frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.data.bulk_fetcher import BinanceBulkFetcher
from core.data.storage import PostgresStorage
# from core.data.strategy_storage import StrategyStorage  # Deprecated - using new strategies table
from core.indicators.technical import add_all_indicators
from core.indicators.regime import detect_market_regimes
from config.config import load_config

app = FastAPI(
    title="Backtesting Research Tool API",
    description="REST API for cryptocurrency backtesting platform",
    version="1.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
config = load_config()

# Pydantic models for request/response
class DataFetchRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str  # ISO format: "2024-01-01"
    end_date: Optional[str] = None

class DataFetchResponse(BaseModel):
    success: bool
    message: str
    candles_fetched: int
    candles_inserted: int

class DataStatsResponse(BaseModel):
    symbol: str
    timeframe: str
    candle_count: int
    first_candle: datetime
    last_candle: datetime

class CandleData(BaseModel):
    time: int  # Unix timestamp in seconds
    open: float
    high: float
    low: float
    close: float
    volume: float

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Backtesting Research Tool API",
        "version": "1.0.0"
    }

@app.get("/api/data/stats")
def get_data_stats() -> List[DataStatsResponse]:
    """Get statistics about stored data in PostgreSQL"""
    try:
        with PostgresStorage(config['database']) as storage:
            df = storage.get_data_stats()

            # Convert DataFrame to list of dicts
            stats = []
            for _, row in df.iterrows():
                stats.append({
                    "symbol": row['symbol'],
                    "timeframe": row['timeframe'],
                    "candle_count": int(row['candle_count']),
                    "first_candle": row['first_candle'],
                    "last_candle": row['last_candle']
                })

            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

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
            end_date=end_date
        )

        if df.empty:
            return DataFetchResponse(
                success=False,
                message="No data fetched from Binance",
                candles_fetched=0,
                candles_inserted=0
            )

        # Store in PostgreSQL
        with PostgresStorage(config['database']) as storage:
            storage.create_tables()
            inserted = storage.insert_candles(df, request.symbol, request.timeframe)

        return DataFetchResponse(
            success=True,
            message=f"Successfully fetched and stored data for {request.symbol}",
            candles_fetched=len(df),
            candles_inserted=inserted
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")

@app.get("/api/data/range/{symbol}/{timeframe}")
def get_data_range(symbol: str, timeframe: str):
    """Get available data range for a symbol/timeframe"""
    try:
        with PostgresStorage(config['database']) as storage:
            range_data = storage.get_available_data_range(symbol, timeframe)

            if range_data is None:
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "has_data": False
                }

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "has_data": True,
                "start_date": range_data[0],
                "end_date": range_data[1]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data range: {str(e)}")

@app.get("/api/data/candles/{symbol}/{timeframe}")
def get_candles(symbol: str, timeframe: str) -> List[CandleData]:
    """Get all candles for a symbol/timeframe for chart visualization"""
    try:
        with PostgresStorage(config['database']) as storage:
            df = storage.get_candles(symbol, timeframe)

            if df.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for {symbol} {timeframe}"
                )

            # Convert DataFrame to list of candle objects
            candles = []
            for _, row in df.iterrows():
                candles.append({
                    "time": int(row['open_time'].timestamp()),  # Convert to Unix timestamp
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume'])
                })

            return candles
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get candles: {str(e)}")

@app.delete("/api/data/{symbol}/{timeframe}")
def delete_data(symbol: str, timeframe: str):
    """Delete all candles for a symbol/timeframe"""
    try:
        with PostgresStorage(config['database']) as storage:
            deleted = storage.delete_candles(symbol, timeframe)

            if deleted == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for {symbol} {timeframe}"
                )

            return {
                "success": True,
                "message": f"Deleted {deleted} candles for {symbol} {timeframe}",
                "deleted_count": deleted
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
        with PostgresStorage(config['database']) as storage:
            # HYBRID MODE: Try database first
            if storage.has_regimes(symbol, timeframe):
                # FAST PATH: Fetch pre-computed regimes (~10ms)
                regimes_df = storage.get_regimes(symbol, timeframe)

                # Map regimes to visualization colors
                regime_colors = {
                    "TREND_UP": "#22c55e",      # Green
                    "TREND_DOWN": "#ef4444",    # Red
                    "RANGE": "#3b82f6",         # Blue
                    "CHOPPY": "#f59e0b",        # Orange
                    "NEUTRAL": "#6b7280"        # Gray
                }

                # Format for frontend
                result = []
                for timestamp, row in regimes_df.iterrows():
                    simplified = row.get('simplified_regime')

                    result.append({
                        "time": int(timestamp.timestamp()),
                        "regime": simplified if not pd.isna(simplified) else "NEUTRAL",
                        "full_regime": row.get('full_regime', ''),
                        "trend_state": row.get('trend_state', ''),
                        "volatility_state": row.get('volatility_state', ''),
                        "momentum_state": row.get('momentum_state', ''),
                        "confidence": float(row.get('confidence', 0.5)),
                        "color": regime_colors.get(simplified, "#6b7280")
                    })

                return result

            # FALLBACK: Compute on-the-fly (~61ms)
            # 1. Fetch candles from database
            df = storage.get_candles(symbol, timeframe)

            if df.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for {symbol} {timeframe}"
                )

            # 2. Add all technical indicators
            df = add_all_indicators(df)

            # 3. Detect market regimes (event-driven, no lookahead)
            df = detect_market_regimes(df)

            # 4. Map regimes to visualization colors
            regime_colors = {
                "TREND_UP": "#22c55e",      # Green
                "TREND_DOWN": "#ef4444",    # Red
                "RANGE": "#3b82f6",         # Blue
                "CHOPPY": "#f59e0b",        # Orange
                "NEUTRAL": "#6b7280"        # Gray
            }

            # 5. Format for frontend
            result = []
            for _, row in df.iterrows():
                simplified = row.get('simplified_regime')

                result.append({
                    "time": int(row['open_time'].timestamp()),
                    "regime": simplified if not pd.isna(simplified) else "NEUTRAL",
                    "full_regime": row.get('full_regime', ''),
                    "trend_state": row.get('trend_state', ''),
                    "volatility_state": row.get('volatility_state', ''),
                    "momentum_state": row.get('momentum_state', ''),
                    "confidence": float(row.get('regime_confidence', 0.5)),
                    "color": regime_colors.get(simplified, "#6b7280")
                })

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get regimes: {str(e)}"
        )

# =============================================================================
# STRATEGY ENDPOINTS
# =============================================================================

class StrategyResponse(BaseModel):
    """Response model for strategy data"""
    name: str
    description: str
    strategy_type: str
    parameters: dict
    regime_filter: Optional[List[str]] = None
    sub_regime_filter: Optional[dict] = None


class CreateStrategyRequest(BaseModel):
    """Request model for creating a composite strategy"""
    name: str
    description: str = ""
    entry_logic: dict  # LogicTree JSON
    exit_logic: dict   # LogicTree JSON
    parameters: Optional[dict] = None
    regime_filter: Optional[List[str]] = None
    sub_regime_filter: Optional[dict] = None


@app.get("/api/strategies", response_model=List[StrategyResponse])
def list_strategies():
    """
    List all available trading strategies.

    Returns strategies from the new 'strategies' table.
    Used by agent tool: list_strategies
    """
    try:
        with PostgresStorage(config['database']) as storage:
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
                    sub_regime_filter=None  # Not used in new schema
                )
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@app.get("/api/strategies/{name}")
def get_strategy(name: str):
    """
    Get detailed information about a specific strategy.

    Used by agent tool: get_strategy
    """
    try:
        with PostgresStorage(config['database']) as storage:
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
                raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")

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
                "updated_at": row[7].isoformat() if row[7] else None
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy: {str(e)}")


@app.post("/api/strategies")
def create_strategy(request: CreateStrategyRequest):
    """
    Create a new composite strategy.

    Used by agent tool: create_strategy
    """
    # TODO: Implement using new strategies table
    raise HTTPException(status_code=501, detail="Strategy creation temporarily disabled during migration to new schema")


@app.delete("/api/strategies/{name}")
def delete_strategy(name: str):
    """Delete a strategy from strategies table"""
    try:
        with PostgresStorage(config['database']) as storage:
            query = "DELETE FROM strategies WHERE name = %s RETURNING id"
            storage.cursor.execute(query, (name,))
            result = storage.cursor.fetchone()
            storage.conn.commit()

            if not result:
                raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")

            return {
                "success": True,
                "message": f"Strategy '{name}' deleted"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete strategy: {str(e)}")


# =============================================================================
# BACKTEST ENDPOINT
# =============================================================================

class BacktestRequest(BaseModel):
    """Request model for running a backtest"""
    strategy_name: str
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    start_date: str  # ISO format: "2024-01-01"
    end_date: Optional[str] = None
    initial_capital: float = 10000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    position_size_pct: float = 1.0
    # Override strategy parameters for this run
    parameters: Optional[dict] = None
    # Override regime filter for this run
    regime_filter: Optional[List[str]] = None


class TradeResult(BaseModel):
    """Single trade result"""
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    duration_hours: float


class BacktestResponse(BaseModel):
    """Response model for backtest results"""
    success: bool
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str

    # Key metrics for AI analysis
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    profit_factor: float

    # Data for visualization
    equity_curve: List[dict]
    trades: List[TradeResult]

    # Regime statistics
    regime_stats: Optional[dict] = None


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
        with PostgresStorage(config['database']) as storage:
            query = """
                SELECT name, class_name, parameters, regime_filter
                FROM strategies
                WHERE name = %s
            """
            storage.cursor.execute(query, (request.strategy_name,))
            row = storage.cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Strategy '{request.strategy_name}' not found. Use list_strategies to see available strategies."
                )

            strategy_name, class_name, parameters, regime_filter = row

        # 2. Check if data exists
        with PostgresStorage(config['database']) as data_storage:
            # Parse dates
            start_dt = datetime.fromisoformat(request.start_date)
            end_dt = datetime.fromisoformat(request.end_date) if request.end_date else None

            # Check data availability
            data_range = data_storage.get_available_data_range(request.symbol, request.timeframe)
            if data_range is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for {request.symbol} {request.timeframe}. Fetch data first using /api/data/fetch."
                )

            # Get candles
            df = data_storage.get_candles(
                request.symbol,
                request.timeframe,
                start_time=start_dt,
                end_time=end_dt
            )

            if df.empty:
                raise HTTPException(
                    status_code=400,
                    detail=f"No candles found for {request.symbol} {request.timeframe} in range {request.start_date} to {request.end_date}"
                )

        # 3. Merge parameters (database params + override params)
        final_params = {**(parameters or {}), **(request.parameters or {})}

        # Apply regime filter override if provided
        final_regime_filter = request.regime_filter if request.regime_filter else regime_filter

        # 4. Instantiate strategy from class name
        from core.backtest.strategies.ma_crossover import MovingAverageCrossover

        # Map class names to actual classes (expand as we add more strategies)
        STRATEGY_CLASSES = {
            'MovingAverageCrossover': MovingAverageCrossover,
        }

        strategy_class = STRATEGY_CLASSES.get(class_name)
        if not strategy_class:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown strategy class: {class_name}. Available: {list(STRATEGY_CLASSES.keys())}"
            )

        strategy = strategy_class(**final_params)

        # Apply regime filter if provided
        if hasattr(strategy, 'regime_filter') and final_regime_filter:
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
            enable_regime_detection=True
        )

        results = engine.run()

        # 6. Get regime stats if available
        regime_stats = None
        if hasattr(strategy, 'get_regime_stats'):
            regime_stats = strategy.get_regime_stats()

        # 7. Format response
        # Get actual date range from data
        actual_start = df.index[0] if hasattr(df.index[0], 'isoformat') else df.iloc[0]['open_time']
        actual_end = df.index[-1] if hasattr(df.index[-1], 'isoformat') else df.iloc[-1]['open_time']

        return BacktestResponse(
            success=True,
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=actual_start.isoformat() if hasattr(actual_start, 'isoformat') else str(actual_start),
            end_date=actual_end.isoformat() if hasattr(actual_end, 'isoformat') else str(actual_end),

            # Metrics
            total_return_pct=round(results['metrics'].get('total_return', 0), 4),
            sharpe_ratio=round(results['metrics'].get('sharpe_ratio', 0), 4),
            max_drawdown_pct=round(results['metrics'].get('max_drawdown', 0), 4),
            win_rate_pct=round(results['metrics'].get('win_rate', 0), 2),
            total_trades=results['metrics'].get('total_trades', 0),
            profit_factor=round(results['metrics'].get('profit_factor', 0), 4),

            # Equity curve for visualization
            equity_curve=[
                {"time": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts), "value": round(val, 2)}
                for ts, val in results['equity_curve']
            ],

            # Trades for analysis
            trades=[
                TradeResult(
                    entry_time=t.entry_time.isoformat() if hasattr(t.entry_time, 'isoformat') else str(t.entry_time),
                    exit_time=t.exit_time.isoformat() if hasattr(t.exit_time, 'isoformat') else str(t.exit_time),
                    entry_price=round(t.entry_price, 2),
                    exit_price=round(t.exit_price, 2),
                    pnl=round(t.pnl, 2),
                    pnl_pct=round(t.return_pct, 4),
                    duration_hours=round(t.duration.total_seconds() / 3600, 2) if hasattr(t.duration, 'total_seconds') else 0
                )
                for t in results['trades']
            ],

            # Regime stats
            regime_stats=regime_stats
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@app.get("/api/data/check/{symbol}/{timeframe}")
def check_data_availability(symbol: str, timeframe: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """
    Check if data is available for backtesting.

    Used by agent to validate before running backtest.
    """
    try:
        with PostgresStorage(config['database']) as storage:
            data_range = storage.get_available_data_range(symbol, timeframe)

            if data_range is None:
                return {
                    "available": False,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "message": "No data found. Use /api/data/fetch to download data."
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
                        "message": f"Requested start date {start_date} is before available data ({data_range[0].date()})"
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
                        "message": f"Requested end date {end_date} is after available data ({data_range[1].date()})"
                    }

            return {
                "available": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data_start": data_range[0].isoformat(),
                "data_end": data_range[1].isoformat(),
                "message": "Data is available for the requested range"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
