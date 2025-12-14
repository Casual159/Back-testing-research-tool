"""
Backtesting Research Agent

AI-powered assistant for designing, testing, and analyzing trading strategies.
"""

from .core import BacktestingAgent, create_agent
from .protocols import AgentProtocol
from .schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentPhase,
    AgentSuggestion,
    BacktestReport,
    Conversation,
    Message,
    ReportSummary,
    ToolCall,
)

__all__ = [
    # Agent
    "BacktestingAgent",
    "AgentProtocol",
    "create_agent",
    # Schemas
    "AgentChatRequest",
    "AgentChatResponse",
    "AgentPhase",
    "AgentSuggestion",
    "BacktestReport",
    "Conversation",
    "Message",
    "ReportSummary",
    "ToolCall",
]
