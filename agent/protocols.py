"""
Agent Protocol - Abstract interface for agent implementations.

This allows swapping between different LLM backends (Anthropic, LangChain, etc.)
without changing the rest of the codebase.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .schemas import AgentChatResponse, Conversation


class AgentProtocol(ABC):
    """Abstract protocol for backtesting agents."""

    @abstractmethod
    async def chat(self, message: str, conversation_id: Optional[UUID] = None) -> AgentChatResponse:
        """
        Process a user message and return agent response.

        Args:
            message: User's message
            conversation_id: Optional ID to continue existing conversation

        Returns:
            AgentChatResponse with message, phase, data, and metadata
        """
        ...

    @abstractmethod
    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.

        Args:
            conversation_id: UUID of the conversation

        Returns:
            Conversation object or None if not found
        """
        ...

    @abstractmethod
    async def list_conversations(self, limit: int = 50) -> list[Conversation]:
        """
        List recent conversations.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of Conversation objects
        """
        ...
