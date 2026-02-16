"""
Pydantic schemas for API request/response validation.

All models include validation rules, constraints, and examples for OpenAPI docs.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# DATA FETCHING SCHEMAS
# =============================================================================


class DataFetchRequest(BaseModel):
    """Request to fetch historical OHLCV data from Binance"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "start_date": "2024-01-01",
                "end_date": "2024-06-01",
            }
        }
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        pattern=r"^[A-Z0-9]+$",
        description="Trading pair symbol (e.g., BTCUSDT, ETHUSDT)",
    )
    timeframe: str = Field(
        ..., pattern=r"^(1m|5m|15m|30m|1h|4h|1d|1w)$", description="Candlestick timeframe"
    )
    start_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date in ISO format (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in ISO format (YYYY-MM-DD). Defaults to today.",
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD")

    @field_validator("end_date")
    @classmethod
    def validate_end_after_start(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return v
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class DataFetchResponse(BaseModel):
    """Response from data fetch operation"""

    success: bool
    message: str
    candles_fetched: int = Field(ge=0, description="Number of candles fetched")
    candles_inserted: int = Field(ge=0, description="Number of candles inserted to DB")


class DataStatsResponse(BaseModel):
    """Statistics about stored historical data"""

    symbol: str
    timeframe: str
    candle_count: int = Field(ge=0)
    first_candle: datetime
    last_candle: datetime


class CandleData(BaseModel):
    """Single OHLCV candle"""

    time: int = Field(..., description="Unix timestamp in seconds")
    open: float = Field(gt=0, description="Open price")
    high: float = Field(gt=0, description="High price")
    low: float = Field(gt=0, description="Low price")
    close: float = Field(gt=0, description="Close price")
    volume: float = Field(ge=0, description="Trading volume")

    @field_validator("high")
    @classmethod
    def validate_high_is_highest(cls, v: float, info) -> float:
        data = info.data
        if "open" in data and "low" in data and "close" in data:
            if v < data["low"]:
                raise ValueError("High must be >= Low")
            if v < min(data["open"], data["close"]):
                raise ValueError("High must be >= Open and Close")
        return v

    @field_validator("low")
    @classmethod
    def validate_low_is_lowest(cls, v: float, info) -> float:
        data = info.data
        if "open" in data and "close" in data:
            if v > max(data["open"], data["close"]):
                raise ValueError("Low must be <= Open and Close")
        return v


# =============================================================================
# STRATEGY SCHEMAS
# =============================================================================


class StrategyResponse(BaseModel):
    """Response model for strategy data"""

    name: str
    description: str
    strategy_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    regime_filter: Optional[List[str]] = None
    sub_regime_filter: Optional[Dict[str, Any]] = None


class CreateStrategyRequest(BaseModel):
    """Request to create a new trading strategy"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My RSI Strategy",
                "description": "RSI reversal with custom parameters",
                "builtin_class": "RSIReversal",
                "parameters": {"period": 14, "oversold": 30, "overbought": 70},
                "regime_filter": ["TREND_UP", "RANGE"],
            }
        }
    )

    name: str = Field(..., min_length=1, max_length=100, description="Unique strategy name")
    description: str = Field(default="", max_length=500, description="Strategy description")
    builtin_class: Optional[str] = Field(
        None,
        pattern=r"^(MovingAverageCrossover|RSIReversal|BollingerBands|MACDCross)$",
        description="Built-in strategy class name",
    )
    entry_logic: Optional[Dict[str, Any]] = Field(
        None, description="Entry logic tree for composite strategies"
    )
    exit_logic: Optional[Dict[str, Any]] = Field(
        None, description="Exit logic tree for composite strategies"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Strategy parameters (e.g., RSI period, MA lengths)"
    )
    regime_filter: Optional[List[str]] = Field(
        None, description="Market regimes where strategy is active"
    )
    sub_regime_filter: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("regime_filter")
    @classmethod
    def validate_regime_filter(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        valid_regimes = {"TREND_UP", "TREND_DOWN", "RANGE", "CHOPPY", "NEUTRAL"}
        for regime in v:
            if regime not in valid_regimes:
                raise ValueError(f"Invalid regime: {regime}. Must be one of {valid_regimes}")
        return v


# =============================================================================
# BACKTEST SCHEMAS
# =============================================================================


class BacktestRequest(BaseModel):
    """Request to run a backtest"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "strategy_name": "RSI Reversal",
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "start_date": "2024-01-01",
                "end_date": "2024-06-01",
                "initial_capital": 10000.0,
                "commission_rate": 0.001,
            }
        }
    )

    strategy_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the strategy to test"
    )
    symbol: str = Field(default="BTCUSDT", pattern=r"^[A-Z0-9]+$", description="Trading pair")
    timeframe: str = Field(
        default="1h", pattern=r"^(1m|5m|15m|30m|1h|4h|1d|1w)$", description="Candlestick timeframe"
    )
    start_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Backtest start date (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Backtest end date (YYYY-MM-DD)"
    )
    initial_capital: float = Field(
        default=10000.0, gt=0, le=10_000_000, description="Starting capital in USD"
    )
    commission_rate: float = Field(
        default=0.001, ge=0, le=0.1, description="Commission rate (0.001 = 0.1%)"
    )
    slippage_rate: float = Field(
        default=0.0005, ge=0, le=0.01, description="Slippage rate (0.0005 = 0.05%)"
    )
    position_size_pct: float = Field(
        default=1.0, gt=0, le=1.0, description="Position size as % of capital (1.0 = 100%)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Override strategy parameters for this run"
    )
    regime_filter: Optional[List[str]] = Field(
        None, description="Override regime filter for this run"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            date = datetime.fromisoformat(v)
            if date > datetime.now():
                raise ValueError("Date cannot be in the future")
            return v
        except ValueError:
            raise ValueError(f"Invalid date: {v}. Use YYYY-MM-DD format")

    @field_validator("end_date")
    @classmethod
    def validate_end_after_start(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return v
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class TradeResult(BaseModel):
    """Single trade result from backtest"""

    entry_time: str
    exit_time: str
    entry_price: float = Field(gt=0)
    exit_price: float = Field(gt=0)
    pnl: float
    pnl_pct: float
    duration_hours: float = Field(ge=0)


class BacktestResponse(BaseModel):
    """Backtest results with metrics and trades"""

    success: bool
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str

    # Performance metrics
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float = Field(ge=0, le=100)
    total_trades: int = Field(ge=0)
    profit_factor: float = Field(ge=0)

    # Visualization data
    equity_curve: List[Dict[str, Any]]
    trades: List[TradeResult]


# =============================================================================
# AGENT SCHEMAS
# =============================================================================


class AgentChatRequest(BaseModel):
    """Request to chat with the AI research agent"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "I want to test a RSI reversal strategy on BTCUSDT",
                "conversation_id": "uuid-here",
            }
        }
    )

    message: str = Field(
        ..., min_length=1, max_length=5000, description="User message to the agent"
    )
    conversation_id: Optional[str] = Field(
        None,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="UUID of existing conversation to continue",
    )
    project_id: Optional[str] = Field(
        None,
        description="Project ID for timeline event creation",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        # Strip whitespace
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        # Check for potentially malicious content
        if re.search(r"<script|javascript:|onerror=", v, re.IGNORECASE):
            raise ValueError("Message contains potentially unsafe content")
        return v


# =============================================================================
# PROJECT MANAGEMENT SCHEMAS
# =============================================================================


class CreateProjectRequest(BaseModel):
    """Request to create a new research project"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    thesis: Optional[str] = Field(None, max_length=2000)
    user_preferences: Optional[Dict[str, Any]] = None


class UpdateProjectRequest(BaseModel):
    """Request to update a project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    thesis: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern=r"^(active|paused|concluded)$")
    validation_result: Optional[str] = Field(
        None, pattern=r"^(validated|invalidated|inconclusive)$"
    )
    notebook: Optional[List[Dict[str, Any]]] = None


class CreateEventRequest(BaseModel):
    """Request to create a timeline event"""

    project_id: int = Field(..., gt=0)
    event_type: str = Field(
        ..., pattern=r"^(backtest|strategy_created|milestone|note)$", description="Type of event"
    )
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# ONBOARDING SCHEMAS
# =============================================================================


class OnboardingPreferencesRequest(BaseModel):
    """User preferences from onboarding wizard"""

    experience_level: str = Field(..., pattern=r"^(beginner|intermediate|advanced)$")
    trading_goals: List[str] = Field(
        ..., min_length=1, max_length=5, description="Selected trading goals"
    )
    preferred_timeframe: str = Field(..., pattern=r"^(1m|5m|15m|30m|1h|4h|1d|1w)$")
    risk_tolerance: str = Field(..., pattern=r"^(low|medium|high)$")


# =============================================================================
# ERROR LOGGING SCHEMAS
# =============================================================================


class LogErrorRequest(BaseModel):
    """Request to log an error"""

    source: str = Field(..., min_length=1, max_length=100)
    tool_name: Optional[str] = Field(None, max_length=100)
    error_type: str = Field(..., min_length=1, max_length=200)
    error_message: str = Field(..., min_length=1, max_length=5000)
    stack_trace: Optional[str] = Field(None, max_length=20000)
    request_data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
