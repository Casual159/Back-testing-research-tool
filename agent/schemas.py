"""
Agent Schemas - Pydantic models for agent communication.

These schemas are framework-agnostic and can be used with any LLM backend.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class AgentPhase(str, Enum):
    """Agent workflow phases."""
    STRATEGY_DESIGN = "STRATEGY_DESIGN"
    STRATEGY_VALIDATION = "STRATEGY_VALIDATION"
    DATA_SELECTION = "DATA_SELECTION"
    BACKTEST_EXECUTION = "BACKTEST_EXECUTION"
    RESULTS_ANALYSIS = "RESULTS_ANALYSIS"
    COMPLETE = "COMPLETE"
    # Free conversation (no specific phase)
    CONVERSATION = "CONVERSATION"


class SuggestionCategory(str, Enum):
    """Categories for agent suggestions."""
    INDICATOR = "indicator"
    METRIC = "metric"
    VISUALIZATION = "visualization"
    STRATEGY = "strategy"
    DATA = "data"
    OTHER = "other"


class SuggestionPriority(str, Enum):
    """Priority levels for suggestions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =============================================================================
# MESSAGE MODELS
# =============================================================================

class ToolCall(BaseModel):
    """Record of a tool call made by the agent."""
    tool_name: str
    arguments: dict[str, Any]
    result: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """A single message in the conversation."""
    role: str  # "user" | "assistant" | "system"
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AgentChatRequest(BaseModel):
    """Request to chat with the agent."""
    message: str
    conversation_id: Optional[UUID] = None


class AgentChatResponse(BaseModel):
    """Response from the agent."""
    # Main response
    message: str
    conversation_id: UUID

    # Agent state
    phase: AgentPhase
    awaiting_confirmation: bool = False
    confirmation_prompt: Optional[str] = None

    # Structured data (for frontend rendering)
    data: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0


# =============================================================================
# CONVERSATION CONTEXT
# =============================================================================

class ConversationContext(BaseModel):
    """Working memory for the agent during a conversation."""
    # Proposed/selected items
    proposed_strategy: Optional[dict[str, Any]] = None
    selected_strategy_name: Optional[str] = None
    proposed_dataset: Optional[dict[str, Any]] = None

    # Pending confirmations
    pending_confirmation: Optional[str] = None  # "strategy" | "data" | "backtest"

    # Results
    last_backtest_id: Optional[UUID] = None
    last_report_id: Optional[UUID] = None


class Conversation(BaseModel):
    """Full conversation state."""
    id: UUID
    messages: list[Message] = Field(default_factory=list)
    phase: AgentPhase = AgentPhase.CONVERSATION
    context: ConversationContext = Field(default_factory=ConversationContext)

    # Usage tracking
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    tool_calls_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# REPORT MODELS
# =============================================================================

class ReportSummary(BaseModel):
    """Summary of a backtest report (for listing)."""
    id: UUID
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    total_return_pct: float
    sharpe_ratio: Optional[float]
    total_trades: int
    created_at: datetime


class BacktestReport(BaseModel):
    """Full backtest report."""
    id: UUID

    # Strategy
    strategy_name: str
    strategy_config: dict[str, Any]

    # Dataset
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float

    # Core metrics
    total_return_pct: float
    sharpe_ratio: Optional[float]
    max_drawdown_pct: Optional[float]
    win_rate_pct: Optional[float]
    total_trades: int
    profit_factor: Optional[float]

    # Extended metrics
    calmar_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    recovery_factor: Optional[float] = None
    avg_trade_duration_hours: Optional[float] = None
    best_trade_pct: Optional[float] = None
    worst_trade_pct: Optional[float] = None
    max_consecutive_wins: Optional[int] = None
    max_consecutive_losses: Optional[int] = None

    # Visualization data
    equity_curve: list[dict[str, Any]] = Field(default_factory=list)
    trades: list[dict[str, Any]] = Field(default_factory=list)
    drawdown_curve: list[dict[str, Any]] = Field(default_factory=list)
    monthly_returns: dict[str, float] = Field(default_factory=dict)

    # Regime analysis
    regime_performance: dict[str, Any] = Field(default_factory=dict)

    # AI interpretation
    ai_summary: Optional[str] = None
    ai_recommendations: list[str] = Field(default_factory=list)
    ai_concerns: list[str] = Field(default_factory=list)

    # Metadata
    conversation_id: Optional[UUID] = None
    created_at: datetime


# =============================================================================
# SUGGESTION MODEL
# =============================================================================

class AgentSuggestion(BaseModel):
    """A feature suggestion from the agent."""
    id: UUID
    conversation_id: Optional[UUID] = None
    report_id: Optional[UUID] = None

    category: SuggestionCategory
    title: str
    description: str
    rationale: Optional[str] = None

    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    status: str = "pending"

    created_at: datetime = Field(default_factory=datetime.utcnow)
