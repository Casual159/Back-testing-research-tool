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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
