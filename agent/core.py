"""
Agent Core - Anthropic Claude implementation of the backtesting agent.

This is the main agent class that orchestrates conversations, tool calls,
and state management.
"""

import json
import os
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

import anthropic
import httpx

from .prompts import get_system_prompt
from .protocols import AgentProtocol
from .schemas import (
    AgentChatResponse,
    AgentPhase,
    Conversation,
    ConversationContext,
    Message,
    ToolCall,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "20"))

# Claude pricing (per 1M tokens) - claude-sonnet-4-20250514
INPUT_COST_PER_1M = 3.0
OUTPUT_COST_PER_1M = 15.0


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOLS = [
    {
        "name": "list_strategies",
        "description": "List all available trading strategies with their descriptions and parameters.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_strategy",
        "description": "Get detailed information about a specific strategy including parameters and regime recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Strategy name (e.g., 'RSI Reversal', 'MA Crossover')"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "check_data",
        "description": "Check if historical data is available for a symbol/timeframe. ALWAYS use this before running a backtest.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair (e.g., 'BTCUSDT')",
                    "default": "BTCUSDT"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                    "description": "Candle timeframe",
                    "default": "1h"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_market_regime",
        "description": "Get current market regime classification (TREND_UP, TREND_DOWN, RANGE, CHOPPY, NEUTRAL). Use this to recommend appropriate strategies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "default": "BTCUSDT"
                },
                "timeframe": {
                    "type": "string",
                    "default": "1h"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_data_stats",
        "description": "Get statistics about all available historical data in the database.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fetch_data",
        "description": """Fetch historical OHLCV data from Binance and store it in the database.

Use this when:
- User wants to test a symbol that doesn't have data yet
- User explicitly asks to download/fetch data
- check_data shows no data available for the requested symbol

This operation may take a few seconds depending on the date range.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair (e.g., 'BTCUSDT', 'ETHUSDT', 'BNBUSDC')"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                    "description": "Candle timeframe",
                    "default": "1h"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD). Default: 6 months ago"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD). Default: today"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "create_strategy",
        "description": """Create a new trading strategy. Use builtin_class for variants of existing strategies, or define custom entry/exit logic.

Builtin classes: MovingAverageCrossover, RSIReversal, BollingerBands, MACDCross

For custom strategies, define entry_logic and exit_logic as condition trees.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique strategy name"
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description"
                },
                "builtin_class": {
                    "type": "string",
                    "enum": ["MovingAverageCrossover", "RSIReversal", "BollingerBands", "MACDCross"],
                    "description": "Base strategy class to use"
                },
                "parameters": {
                    "type": "object",
                    "description": "Strategy parameters (e.g., {fast_period: 10, slow_period: 30})"
                },
                "regime_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only trade in these regimes: TREND_UP, TREND_DOWN, RANGE, CHOPPY, NEUTRAL"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "run_backtest",
        "description": """Run a backtest with a strategy on historical data. Returns performance metrics, trades, and equity curve.

IMPORTANT: Check data availability first with check_data tool.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy_name": {
                    "type": "string",
                    "description": "Name of the strategy to test"
                },
                "symbol": {
                    "type": "string",
                    "default": "BTCUSDT"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1h", "4h", "1d"],
                    "default": "1h"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)"
                },
                "initial_capital": {
                    "type": "number",
                    "default": 10000
                },
                "regime_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only trade in specific regimes"
                },
                "parameters": {
                    "type": "object",
                    "description": "Override strategy parameters"
                }
            },
            "required": ["strategy_name", "start_date"]
        }
    },
    {
        "name": "save_report",
        "description": "Save backtest results as a persistent report for future reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "backtest_results": {
                    "type": "object",
                    "description": "Results from run_backtest"
                },
                "ai_summary": {
                    "type": "string",
                    "description": "Your interpretation of the results"
                },
                "ai_recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of recommendations"
                },
                "ai_concerns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of concerns or warnings"
                }
            },
            "required": ["backtest_results"]
        }
    },
    {
        "name": "suggest_enhancement",
        "description": "Record a suggestion for improving the backtesting tool. Use this when you identify missing features that would help analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["indicator", "metric", "visualization", "strategy", "data", "other"],
                    "description": "Type of enhancement"
                },
                "title": {
                    "type": "string",
                    "description": "Short title for the suggestion"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of what's needed"
                },
                "rationale": {
                    "type": "string",
                    "description": "Why this would be useful"
                }
            },
            "required": ["category", "title", "description"]
        }
    },
    {
        "name": "list_reports",
        "description": """List saved backtest reports.

Returns recent backtest reports with key metrics:
- id: Report UUID (use with get_report for full details)
- strategy_name: Strategy that was tested
- symbol, timeframe: Market data used
- total_return_pct, sharpe_ratio: Key performance metrics
- total_trades: Number of trades executed
- created_at: When the backtest was run

Use this to browse previous backtest results and find interesting reports to analyze in detail.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of reports to return (default: 20)",
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "get_report",
        "description": """Get full details of a saved backtest report.

Returns complete report including:
- All performance metrics (return, Sharpe, drawdown, win rate, profit factor)
- Equity curve data for visualization
- Trade history with entry/exit prices and P&L
- AI analysis if available (summary, recommendations, concerns)
- Regime performance breakdown

Use the report ID from list_reports to fetch specific reports.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "report_id": {
                    "type": "string",
                    "description": "UUID of the report to retrieve"
                }
            },
            "required": ["report_id"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION
# =============================================================================

async def execute_tool(tool_name: str, arguments: dict[str, Any], conversation_id: Optional[UUID] = None) -> dict[str, Any]:
    """Execute a tool by calling the API."""
    from urllib.parse import quote

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            if tool_name == "list_strategies":
                response = await client.get(f"{API_BASE_URL}/api/strategies")

            elif tool_name == "get_strategy":
                name = quote(arguments["name"], safe='')
                response = await client.get(f"{API_BASE_URL}/api/strategies/{name}")

            elif tool_name == "check_data":
                symbol = arguments.get("symbol", "BTCUSDT")
                timeframe = arguments.get("timeframe", "1h")
                params = {}
                if "start_date" in arguments:
                    params["start_date"] = arguments["start_date"]
                if "end_date" in arguments:
                    params["end_date"] = arguments["end_date"]
                response = await client.get(
                    f"{API_BASE_URL}/api/data/check/{symbol}/{timeframe}",
                    params=params
                )

            elif tool_name == "get_market_regime":
                symbol = arguments.get("symbol", "BTCUSDT")
                timeframe = arguments.get("timeframe", "1h")
                response = await client.get(
                    f"{API_BASE_URL}/api/data/regime/{symbol}/{timeframe}"
                )
                data = response.json()
                if isinstance(data, list) and len(data) > 5:
                    return {
                        "current_regime": data[-1] if data else None,
                        "recent_regimes": data[-5:],
                        "total_entries": len(data)
                    }
                return data

            elif tool_name == "get_data_stats":
                response = await client.get(f"{API_BASE_URL}/api/data/stats")

            elif tool_name == "fetch_data":
                # Calculate default dates if not provided
                from datetime import timedelta
                today = datetime.now()
                six_months_ago = today - timedelta(days=180)

                fetch_request = {
                    "symbol": arguments["symbol"],
                    "timeframe": arguments.get("timeframe", "1h"),
                    "start_date": arguments.get("start_date", six_months_ago.strftime("%Y-%m-%d")),
                    "end_date": arguments.get("end_date", today.strftime("%Y-%m-%d"))
                }
                response = await client.post(
                    f"{API_BASE_URL}/api/data/fetch",
                    json=fetch_request,
                    timeout=300.0  # Data fetch can take longer
                )

            elif tool_name == "create_strategy":
                response = await client.post(
                    f"{API_BASE_URL}/api/strategies",
                    json=arguments
                )

            elif tool_name == "run_backtest":
                response = await client.post(
                    f"{API_BASE_URL}/api/backtest",
                    json=arguments
                )

            elif tool_name == "save_report":
                # Save to reports table
                response = await client.post(
                    f"{API_BASE_URL}/api/reports",
                    json={
                        **arguments,
                        "conversation_id": str(conversation_id) if conversation_id else None
                    }
                )

            elif tool_name == "suggest_enhancement":
                # Save to suggestions table
                response = await client.post(
                    f"{API_BASE_URL}/api/suggestions",
                    json={
                        **arguments,
                        "conversation_id": str(conversation_id) if conversation_id else None
                    }
                )

            elif tool_name == "list_reports":
                limit = arguments.get("limit", 20)
                response = await client.get(
                    f"{API_BASE_URL}/api/reports",
                    params={"limit": limit}
                )

            elif tool_name == "get_report":
                report_id = arguments["report_id"]
                response = await client.get(f"{API_BASE_URL}/api/reports/{report_id}")

            else:
                return {"error": f"Unknown tool: {tool_name}"}

            if response.status_code >= 400:
                error_detail = "Unknown error"
                try:
                    error_detail = response.json().get("detail", error_detail)
                except Exception:
                    error_detail = response.text
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "detail": error_detail
                }

            return response.json()

        except httpx.ConnectError:
            return {
                "error": True,
                "detail": "Cannot connect to API server. Make sure FastAPI is running on localhost:8000"
            }
        except httpx.TimeoutException:
            return {
                "error": True,
                "detail": "API request timed out"
            }


# =============================================================================
# CONVERSATION STORAGE (SINGLETON)
# =============================================================================

class ConversationStorage:
    """
    Singleton in-memory storage for conversations.

    This ensures conversations persist across API requests.
    For production, replace with database-backed storage.
    """
    _instance: Optional["ConversationStorage"] = None
    _conversations: dict[UUID, Conversation] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get(self, conversation_id: UUID) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    async def save(self, conversation: Conversation) -> None:
        conversation.updated_at = datetime.utcnow()
        self._conversations[conversation.id] = conversation

    async def list(self, limit: int = 50) -> list[Conversation]:
        convs = sorted(
            self._conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True
        )
        return convs[:limit]

    async def create(self) -> Conversation:
        conv = Conversation(id=uuid4())
        self._conversations[conv.id] = conv
        return conv

    def clear(self) -> None:
        """Clear all conversations (useful for testing)."""
        self._conversations.clear()


# =============================================================================
# AGENT IMPLEMENTATION
# =============================================================================

class BacktestingAgent(AgentProtocol):
    """Anthropic Claude implementation of the backtesting agent."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        # Sync client for non-streaming
        self.client = anthropic.Anthropic(api_key=self.api_key)
        # Async client for streaming
        self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.storage = ConversationStorage()
        self.model = "claude-sonnet-4-20250514"

    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[UUID] = None
    ):
        """
        Process a user message with streaming response.

        Yields events:
        - {"type": "conversation_id", "id": "uuid"}
        - {"type": "text_delta", "delta": "..."}
        - {"type": "tool_start", "tool": "name", "args": {...}}
        - {"type": "tool_result", "tool": "name", "result": {...}, "success": bool}
        - {"type": "done", "phase": "...", "tokens": int, "cost": float}
        - {"type": "error", "message": "..."}
        """
        try:
            # Get or create conversation
            if conversation_id:
                conversation = await self.storage.get(conversation_id)
                if not conversation:
                    conversation = await self.storage.create()
            else:
                conversation = await self.storage.create()

            # Emit conversation ID first
            yield {"type": "conversation_id", "id": str(conversation.id)}

            # Add user message
            user_message = Message(role="user", content=message)
            conversation.messages.append(user_message)

            # Build messages for Claude
            claude_messages = self._build_claude_messages(conversation)

            # Track usage
            total_input_tokens = 0
            total_output_tokens = 0
            tool_calls: list[ToolCall] = []
            full_text_response = ""

            # Agentic loop with streaming
            iterations = 0
            while iterations < MAX_ITERATIONS:
                iterations += 1

                # Stream Claude response using async client
                current_text = ""
                async with self.async_client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=get_system_prompt(),
                    tools=TOOLS,
                    messages=claude_messages
                ) as stream:
                    # Stream text deltas as they arrive
                    async for event in stream:
                        # Handle text deltas
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, 'text'):
                                current_text += event.delta.text
                                yield {"type": "text_delta", "delta": event.delta.text}

                    # Get final message to check for tool use
                    response = await stream.get_final_message()

                # Track tokens
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                full_text_response += current_text

                # Process response for tool calls
                assistant_content = []
                has_tool_use = False

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        has_tool_use = True
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })

                # Add assistant message to conversation
                claude_messages.append({"role": "assistant", "content": assistant_content})

                # If no tool use, we're done
                if not has_tool_use:
                    break

                # Execute tool calls with streaming updates
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        # Emit tool start
                        yield {
                            "type": "tool_start",
                            "tool": block.name,
                            "args": block.input
                        }

                        # Special handling for fetch_data - stream progress
                        if block.name == "fetch_data":
                            result = None
                            async for event in self._fetch_data_with_progress(block.input):
                                if event["type"] == "progress":
                                    yield {
                                        "type": "tool_progress",
                                        "tool": block.name,
                                        "current": event["current"],
                                        "total": event["total"],
                                        "pct": event["pct"]
                                    }
                                elif event["type"] == "done":
                                    result = event["result"]
                                elif event["type"] == "error":
                                    result = {"error": True, "detail": event["message"]}

                            if result is None:
                                result = {"error": True, "detail": "No result from fetch"}
                        else:
                            # Execute tool normally
                            result = await execute_tool(
                                block.name,
                                block.input,
                                conversation.id
                            )

                        # Check if error
                        is_error = isinstance(result, dict) and result.get("error")

                        # Emit tool result
                        yield {
                            "type": "tool_result",
                            "tool": block.name,
                            "result": self._summarize_tool_result(block.name, result),
                            "success": not is_error
                        }

                        # Truncate result for context efficiency
                        truncated_result = self._truncate_for_context(block.name, result)

                        tool_calls.append(ToolCall(
                            tool_name=block.name,
                            arguments=block.input,
                            result=truncated_result  # Store truncated version
                        ))

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(truncated_result, default=str)
                        })

                # Add tool results
                claude_messages.append({"role": "user", "content": tool_results})
                conversation.tool_calls_count += len(tool_results)

            # Save assistant message to conversation
            assistant_message = Message(
                role="assistant",
                content=full_text_response,
                tool_calls=tool_calls
            )
            conversation.messages.append(assistant_message)

            # Update usage
            conversation.total_tokens += total_input_tokens + total_output_tokens
            cost = (total_input_tokens * INPUT_COST_PER_1M / 1_000_000 +
                    total_output_tokens * OUTPUT_COST_PER_1M / 1_000_000)
            conversation.total_cost_usd += cost

            # Detect phase
            phase, awaiting_confirmation, confirmation_prompt = self._detect_phase(
                full_text_response, tool_calls
            )
            conversation.phase = phase

            # Save conversation
            await self.storage.save(conversation)

            # Emit done event
            yield {
                "type": "done",
                "conversation_id": str(conversation.id),
                "phase": phase.value,
                "awaiting_confirmation": awaiting_confirmation,
                "confirmation_prompt": confirmation_prompt,
                "tokens_used": total_input_tokens + total_output_tokens,
                "cost_usd": cost,
                "data": self._extract_data(tool_calls)
            }

        except Exception as e:
            yield {"type": "error", "message": str(e)}

    def _summarize_tool_result(self, tool_name: str, result: dict) -> dict:
        """Create a summary of tool result for streaming UI."""
        if isinstance(result, dict) and result.get("error"):
            return {"error": result.get("detail", "Unknown error")}

        if tool_name == "run_backtest":
            return {
                "strategy_name": result.get("strategy_name"),
                "symbol": result.get("symbol"),
                "report_id": result.get("report_id"),
                "total_return_pct": result.get("total_return_pct"),
                "sharpe_ratio": result.get("sharpe_ratio"),
                "total_trades": result.get("total_trades"),
                "win_rate_pct": result.get("win_rate_pct"),
                "metrics": {
                    "total_return_pct": result.get("total_return_pct"),
                    "sharpe_ratio": result.get("sharpe_ratio"),
                    "total_trades": result.get("total_trades")
                }
            }
        elif tool_name == "list_strategies":
            strategies = result if isinstance(result, list) else []
            return {"count": len(strategies), "names": [s.get("name") for s in strategies[:5]]}
        elif tool_name == "check_data":
            return {
                "available": result.get("available"),
                "start": result.get("data_start"),
                "end": result.get("data_end")
            }
        elif tool_name == "fetch_data":
            return {
                "success": result.get("success"),
                "candles": result.get("candles_fetched", 0)
            }
        elif tool_name == "create_strategy":
            return {"success": result.get("success"), "name": result.get("strategy", {}).get("name")}
        elif tool_name == "list_reports":
            reports = result if isinstance(result, list) else []
            return {"count": len(reports)}
        elif tool_name == "get_report":
            return {
                "strategy": result.get("strategy_name"),
                "return": result.get("total_return_pct"),
                "sharpe": result.get("sharpe_ratio"),
                "trades": result.get("total_trades")
            }
        else:
            # Generic summary - just indicate success
            return {"success": True}

    async def _fetch_data_with_progress(self, arguments: dict):
        """
        Fetch data using SSE stream and yield progress events.

        Yields:
            {"type": "progress", "current": N, "total": M, "pct": 0-100}
            {"type": "done", "result": {...}}
            {"type": "error", "message": "..."}
        """
        from datetime import timedelta

        # Calculate default dates if not provided
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)

        fetch_request = {
            "symbol": arguments["symbol"],
            "timeframe": arguments.get("timeframe", "1h"),
            "start_date": arguments.get("start_date", six_months_ago.strftime("%Y-%m-%d")),
            "end_date": arguments.get("end_date", today.strftime("%Y-%m-%d"))
        }

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{API_BASE_URL}/api/data/fetch/stream",
                    json=fetch_request
                ) as response:
                    if response.status_code >= 400:
                        yield {"type": "error", "message": f"HTTP {response.status_code}"}
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue

                        try:
                            data = json.loads(line[6:])  # Skip "data: " prefix
                            if data.get("type") == "progress":
                                yield {
                                    "type": "progress",
                                    "current": data.get("current", 0),
                                    "total": data.get("total", 1),
                                    "pct": data.get("pct", 0)
                                }
                            elif data.get("type") == "done":
                                yield {
                                    "type": "done",
                                    "result": {
                                        "success": data.get("success", False),
                                        "candles_fetched": data.get("candles_fetched", 0),
                                        "candles_inserted": data.get("candles_inserted", 0),
                                        "symbol": fetch_request["symbol"],
                                        "timeframe": fetch_request["timeframe"]
                                    }
                                }
                            elif data.get("type") == "error":
                                yield {"type": "error", "message": data.get("message", "Unknown error")}
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            yield {"type": "error", "message": "Cannot connect to API server"}
        except httpx.TimeoutException:
            yield {"type": "error", "message": "Request timed out"}
        except Exception as e:
            yield {"type": "error", "message": str(e)}

    def _truncate_for_context(self, tool_name: str, result: dict) -> dict:
        """
        Truncate tool results to reduce context size.
        Removes large data (equity curves, trades) while keeping essential info.
        """
        if not isinstance(result, dict):
            return result

        if result.get("error"):
            return result

        if tool_name == "run_backtest":
            # Keep metrics, remove large data
            truncated = {
                "success": result.get("success"),
                "strategy_name": result.get("strategy_name"),
                "symbol": result.get("symbol"),
                "timeframe": result.get("timeframe"),
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "total_return_pct": result.get("total_return_pct"),
                "sharpe_ratio": result.get("sharpe_ratio"),
                "max_drawdown_pct": result.get("max_drawdown_pct"),
                "win_rate_pct": result.get("win_rate_pct"),
                "total_trades": result.get("total_trades"),
                "profit_factor": result.get("profit_factor"),
                "report_id": result.get("report_id"),
                # Summarize regime stats if present
                "regime_stats": result.get("regime_stats"),
            }
            # Remove None values
            return {k: v for k, v in truncated.items() if v is not None}

        elif tool_name == "list_strategies":
            # Strategies list is usually fine, but limit if too many
            if isinstance(result, list) and len(result) > 20:
                return result[:20] + [{"note": f"... and {len(result) - 20} more"}]
            return result

        elif tool_name == "get_data_stats":
            # Keep summary, limit detailed stats
            if isinstance(result, dict) and "stats" in result:
                stats = result.get("stats", [])
                if len(stats) > 10:
                    result = dict(result)
                    result["stats"] = stats[:10]
                    result["note"] = f"Showing 10 of {len(stats)} datasets"
            return result

        elif tool_name == "get_report":
            # Keep metrics, truncate large data arrays
            if not isinstance(result, dict):
                return result

            truncated = dict(result)

            # Summarize equity curve (keep start, end, min, max)
            equity_curve = truncated.get("equity_curve", [])
            if isinstance(equity_curve, list) and len(equity_curve) > 10:
                values = [e.get("value", 0) for e in equity_curve if isinstance(e, dict)]
                truncated["equity_curve_summary"] = {
                    "points": len(equity_curve),
                    "start_value": values[0] if values else None,
                    "end_value": values[-1] if values else None,
                    "min_value": min(values) if values else None,
                    "max_value": max(values) if values else None,
                }
                del truncated["equity_curve"]

            # Summarize trades (keep first 5, last 5, and stats)
            trades = truncated.get("trades", [])
            if isinstance(trades, list) and len(trades) > 10:
                truncated["trades_summary"] = {
                    "total": len(trades),
                    "first_5": trades[:5],
                    "last_5": trades[-5:],
                }
                del truncated["trades"]

            return truncated

        elif tool_name == "list_reports":
            # List reports is usually small, but limit if too many
            if isinstance(result, list) and len(result) > 30:
                return result[:30] + [{"note": f"... and {len(result) - 30} more reports"}]
            return result

        # For other tools, return as-is (they're usually small)
        return result

    async def chat(
        self,
        message: str,
        conversation_id: Optional[UUID] = None
    ) -> AgentChatResponse:
        """Process a user message and return agent response (non-streaming)."""

        # Get or create conversation
        if conversation_id:
            conversation = await self.storage.get(conversation_id)
            if not conversation:
                conversation = await self.storage.create()
        else:
            conversation = await self.storage.create()

        # Add user message
        user_message = Message(role="user", content=message)
        conversation.messages.append(user_message)

        # Build messages for Claude
        claude_messages = self._build_claude_messages(conversation)

        # Track usage
        total_input_tokens = 0
        total_output_tokens = 0
        tool_calls: list[ToolCall] = []

        # Agentic loop
        iterations = 0
        while iterations < MAX_ITERATIONS:
            iterations += 1

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=get_system_prompt(),
                tools=TOOLS,
                messages=claude_messages
            )

            # Track tokens
            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            # Process response
            assistant_content = []
            text_response = ""
            has_tool_use = False

            for block in response.content:
                if block.type == "text":
                    text_response += block.text
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    has_tool_use = True
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            # Add assistant message
            claude_messages.append({"role": "assistant", "content": assistant_content})

            # If no tool use, we're done
            if not has_tool_use:
                break

            # Execute tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(
                        block.name,
                        block.input,
                        conversation.id
                    )

                    # Truncate result for context efficiency
                    truncated_result = self._truncate_for_context(block.name, result)

                    tool_calls.append(ToolCall(
                        tool_name=block.name,
                        arguments=block.input,
                        result=truncated_result
                    ))

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(truncated_result, default=str)
                    })

            # Add tool results
            claude_messages.append({"role": "user", "content": tool_results})

            conversation.tool_calls_count += len(tool_results)

        # Save assistant message to conversation
        assistant_message = Message(
            role="assistant",
            content=text_response,
            tool_calls=tool_calls
        )
        conversation.messages.append(assistant_message)

        # Update usage
        conversation.total_tokens += total_input_tokens + total_output_tokens
        cost = (total_input_tokens * INPUT_COST_PER_1M / 1_000_000 +
                total_output_tokens * OUTPUT_COST_PER_1M / 1_000_000)
        conversation.total_cost_usd += cost

        # Detect phase and confirmations
        phase, awaiting_confirmation, confirmation_prompt = self._detect_phase(
            text_response, tool_calls
        )
        conversation.phase = phase

        # Save conversation
        await self.storage.save(conversation)

        return AgentChatResponse(
            message=text_response,
            conversation_id=conversation.id,
            phase=phase,
            awaiting_confirmation=awaiting_confirmation,
            confirmation_prompt=confirmation_prompt,
            data=self._extract_data(tool_calls),
            tool_calls=tool_calls,
            tokens_used=total_input_tokens + total_output_tokens,
            cost_usd=cost
        )

    def _build_claude_messages(self, conversation: Conversation) -> list[dict]:
        """
        Convert conversation to Claude message format with sliding window.
        Keeps only the most recent messages to stay within context limits.
        """
        # Max turns to keep (user + assistant pairs)
        MAX_HISTORY_TURNS = 10

        messages = []
        for msg in conversation.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # If too many messages, keep only recent ones
        # Note: messages alternate user/assistant, so we count pairs
        if len(messages) > MAX_HISTORY_TURNS * 2:
            # Keep system context: first user message + last N turns
            first_msg = messages[0] if messages else None
            recent_messages = messages[-(MAX_HISTORY_TURNS * 2):]

            if first_msg and first_msg not in recent_messages:
                # Add summary of earlier context
                summary = {
                    "role": "user",
                    "content": "[Earlier conversation truncated for context efficiency. The conversation started with the first user message shown above.]"
                }
                messages = [first_msg, summary] + recent_messages
            else:
                messages = recent_messages

        return messages

    def _detect_phase(
        self,
        response: str,
        tool_calls: list[ToolCall]
    ) -> tuple[AgentPhase, bool, Optional[str]]:
        """Detect current phase and if we're awaiting confirmation."""

        response_lower = response.lower()
        tool_names = [tc.tool_name for tc in tool_calls]

        # Confirmation only for destructive/expensive actions
        # Check if agent is about to run backtest or create strategy
        awaiting = False
        confirmation_prompt = None

        # Only show confirmation when agent explicitly asks before action
        action_phrases = [
            ("run this backtest", "Run backtest?"),
            ("run the backtest", "Run backtest?"),
            ("execute the backtest", "Run backtest?"),
            ("create this strategy", "Create strategy?"),
            ("register this strategy", "Create strategy?"),
        ]

        for phrase, prompt in action_phrases:
            if phrase in response_lower:
                awaiting = True
                confirmation_prompt = prompt
                break

        # Detect phase based on tool calls and response content
        if "run_backtest" in tool_names:
            return AgentPhase.BACKTEST_EXECUTION, False, None  # Already ran, no confirmation needed

        if "save_report" in tool_names:
            return AgentPhase.RESULTS_ANALYSIS, False, None

        if "create_strategy" in tool_names:
            return AgentPhase.STRATEGY_VALIDATION, False, None  # Already created

        if any(t in tool_names for t in ["check_data", "get_data_stats", "fetch_data"]):
            return AgentPhase.DATA_SELECTION, awaiting, confirmation_prompt

        if any(t in tool_names for t in ["list_strategies", "get_strategy", "get_market_regime"]):
            return AgentPhase.STRATEGY_DESIGN, awaiting, confirmation_prompt

        # Check response content for phase hints (simplified)
        if any(w in response_lower for w in ["sharpe", "drawdown", "performance", "result"]):
            return AgentPhase.RESULTS_ANALYSIS, awaiting, confirmation_prompt

        if any(w in response_lower for w in ["strategy", "indicator"]):
            return AgentPhase.STRATEGY_DESIGN, awaiting, confirmation_prompt

        return AgentPhase.CONVERSATION, awaiting, confirmation_prompt

    def _extract_data(self, tool_calls: list[ToolCall]) -> dict[str, Any]:
        """Extract structured data from tool call results."""
        data = {}

        for tc in tool_calls:
            result = tc.result
            # Check if result is an error
            is_error = isinstance(result, dict) and result.get("error")

            if tc.tool_name == "run_backtest" and not is_error:
                data["backtest_results"] = result
            elif tc.tool_name == "list_strategies":
                data["strategies"] = result
            elif tc.tool_name == "get_market_regime":
                data["market_regime"] = result
            elif tc.tool_name == "check_data":
                data["data_availability"] = result
            elif tc.tool_name == "save_report":
                data["saved_report"] = result
            elif tc.tool_name == "list_reports":
                data["reports_list"] = result
            elif tc.tool_name == "get_report":
                data["report_detail"] = result

        return data

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Retrieve a conversation by ID."""
        return await self.storage.get(conversation_id)

    async def list_conversations(self, limit: int = 50) -> list[Conversation]:
        """List recent conversations."""
        return await self.storage.list(limit)


# =============================================================================
# FACTORY
# =============================================================================

def create_agent(api_key: Optional[str] = None) -> BacktestingAgent:
    """Create a backtesting agent instance."""
    return BacktestingAgent(api_key=api_key)
