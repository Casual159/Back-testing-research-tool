"""
FastAPI Backend for Backtesting Research Tool
Provides REST API endpoints for the Next.js frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
import httpx
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.data.bulk_fetcher import BinanceBulkFetcher
from core.data.storage import PostgresStorage
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

# Langflow configuration from environment variables
LANGFLOW_URL = os.getenv("LANGFLOW_URL", "http://localhost:7860")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY", "")
FLOW_ID = os.getenv("FLOW_ID", "d77818b2-ddfc-4d08-bfc4-e8b1807a544c")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    message: str
    session_id: Optional[str] = None
    timestamp: datetime
    success: bool = True

# Agent Tool Request/Response Models
class AgentFetchDataRequest(BaseModel):
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AgentToolResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str

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

# ============================================================================
# AGENT TOOLS ENDPOINTS
# ============================================================================

@app.get("/api/agent/tools/data-stats")
def agent_get_data_stats() -> AgentToolResponse:
    """
    Agent Tool: Get statistics about available data in the database

    Returns information about all symbols, timeframes, candle counts, and date ranges.
    This tool requires no parameters.
    """
    try:
        with PostgresStorage(config['database']) as storage:
            df = storage.get_data_stats()

            if df.empty:
                return AgentToolResponse(
                    success=True,
                    data={"stats": []},
                    message="No data found in database"
                )

            # Convert DataFrame to list of dicts with calculated date range
            stats = []
            for _, row in df.iterrows():
                first_candle = row['first_candle']
                last_candle = row['last_candle']
                date_range_days = (last_candle - first_candle).days if first_candle and last_candle else 0

                stats.append({
                    "symbol": row['symbol'],
                    "timeframe": row['timeframe'],
                    "candle_count": int(row['candle_count']),
                    "first_candle": first_candle.isoformat() if first_candle else None,
                    "last_candle": last_candle.isoformat() if last_candle else None,
                    "date_range_days": date_range_days
                })

            return AgentToolResponse(
                success=True,
                data={"stats": stats},
                message=f"Found {len(stats)} dataset(s) in database"
            )
    except Exception as e:
        logger.error(f"Error in agent_get_data_stats: {str(e)}")
        return AgentToolResponse(
            success=False,
            error=str(e),
            message="Failed to retrieve data statistics"
        )

@app.post("/api/agent/tools/fetch-data")
def agent_fetch_data(request: AgentFetchDataRequest) -> AgentToolResponse:
    """
    Agent Tool: Fetch historical data from Binance

    Required parameters:
    - symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
    - timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
    - start_date: Start date in YYYY-MM-DD format
    - end_date: End date in YYYY-MM-DD format

    If any required parameter is missing, the tool will return an error
    indicating which parameters are needed.
    """
    try:
        # Validate all required parameters are provided
        missing_params = []
        if not request.symbol:
            missing_params.append("symbol")
        if not request.timeframe:
            missing_params.append("timeframe")
        if not request.start_date:
            missing_params.append("start_date")
        if not request.end_date:
            missing_params.append("end_date")

        if missing_params:
            return AgentToolResponse(
                success=False,
                error="missing_parameters",
                data={
                    "missing_parameters": missing_params,
                    "required_parameters": {
                        "symbol": "Trading pair (e.g., BTCUSDT, ETHUSDT)",
                        "timeframe": "Candle timeframe (e.g., 1h, 4h, 1d)",
                        "start_date": "Start date in YYYY-MM-DD format",
                        "end_date": "End date in YYYY-MM-DD format"
                    },
                    "provided_parameters": {
                        "symbol": request.symbol,
                        "timeframe": request.timeframe,
                        "start_date": request.start_date,
                        "end_date": request.end_date
                    }
                },
                message=f"Missing required parameters: {', '.join(missing_params)}. Please ask the user for these values."
            )

        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)

        # Validate date range
        if end_date < start_date:
            return AgentToolResponse(
                success=False,
                error="invalid_date_range",
                message="End date must be after start date"
            )

        # Fetch data
        logger.info(f"Fetching data: {request.symbol} {request.timeframe} from {request.start_date} to {request.end_date}")
        fetcher = BinanceBulkFetcher()
        df = fetcher.fetch_historical(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            return AgentToolResponse(
                success=False,
                error="no_data_fetched",
                message=f"No data available from Binance for {request.symbol} {request.timeframe} in the specified date range"
            )

        # Store in PostgreSQL
        with PostgresStorage(config['database']) as storage:
            storage.create_tables()
            inserted = storage.insert_candles(df, request.symbol, request.timeframe)

        return AgentToolResponse(
            success=True,
            data={
                "symbol": request.symbol,
                "timeframe": request.timeframe,
                "candles_fetched": len(df),
                "candles_inserted": inserted,
                "date_range": {
                    "start": request.start_date,
                    "end": request.end_date
                }
            },
            message=f"Successfully fetched {len(df)} candles for {request.symbol} {request.timeframe} and inserted {inserted} into database"
        )

    except ValueError as e:
        return AgentToolResponse(
            success=False,
            error="invalid_format",
            message=f"Invalid parameter format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in agent_fetch_data: {str(e)}")
        return AgentToolResponse(
            success=False,
            error=str(e),
            message=f"Failed to fetch data: {str(e)}"
        )

# ============================================================================
# CHAT / LANGFLOW ENDPOINTS
# ============================================================================

async def call_langflow(message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Call Langflow API to process a message through the Agent workflow

    Args:
        message: User message to send to the agent
        session_id: Optional session ID for conversation continuity

    Returns:
        Dict containing the agent's response and metadata
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "input_value": message,
                "output_type": "chat",
                "input_type": "chat",
            }

            # Add session_id if provided for conversation continuity
            if session_id:
                payload["session_id"] = session_id

            # Prepare headers with API key if available
            headers = {"Content-Type": "application/json"}
            if LANGFLOW_API_KEY:
                headers["x-api-key"] = LANGFLOW_API_KEY

            logger.info(f"Calling Langflow API with message: {message[:50]}...")

            response = await client.post(
                f"{LANGFLOW_URL}/api/v1/run/{FLOW_ID}",
                json=payload,
                headers=headers
            )

            response.raise_for_status()
            data = response.json()

            logger.info(f"Langflow response received: {str(data)[:100]}...")

            # Extract the message from Langflow response
            # Structure: data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
            try:
                outputs = data.get("outputs", [])
                if outputs and len(outputs) > 0:
                    output = outputs[0]
                    if "outputs" in output and len(output["outputs"]) > 0:
                        result = output["outputs"][0]
                        if "results" in result:
                            message_data = result["results"].get("message", {})
                            response_text = message_data.get("text", "")

                            if response_text:
                                return {
                                    "message": response_text,
                                    "session_id": data.get("session_id"),
                                    "success": True
                                }

                # Fallback: try to get any text from the response
                logger.warning("Could not extract message from standard path, trying fallback")
                return {
                    "message": str(data),
                    "session_id": data.get("session_id"),
                    "success": True
                }

            except Exception as e:
                logger.error(f"Error extracting message from Langflow response: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error parsing Langflow response: {str(e)}"
                )

    except httpx.TimeoutException:
        logger.error("Langflow request timed out")
        raise HTTPException(
            status_code=504,
            detail="Langflow agent did not respond in time (120s timeout)"
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Langflow: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Langflow: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error calling Langflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.post("/api/chat/send")
async def send_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    """
    Send a message to the Langflow agent and get a response
    """
    try:
        result = await call_langflow(request.message, request.session_id)

        return ChatMessageResponse(
            message=result["message"],
            session_id=result.get("session_id"),
            timestamp=datetime.now(),
            success=result["success"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_chat_message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.get("/api/chat/health")
async def check_langflow_health():
    """
    Check if Langflow is accessible and responding
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LANGFLOW_URL}/health")
            response.raise_for_status()
            return {
                "status": "ok",
                "langflow_url": LANGFLOW_URL,
                "flow_id": FLOW_ID
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Langflow not accessible: {str(e)}",
            "langflow_url": LANGFLOW_URL
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
