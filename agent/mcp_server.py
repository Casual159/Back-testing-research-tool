"""
MCP Server for Backtesting Research Tool

Exposes backtesting tools via Model Context Protocol for Claude Code integration.
"""

import asyncio
import json
import sys
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# =============================================================================
# CONFIGURATION
# =============================================================================

API_BASE_URL = "http://localhost:8000"


# =============================================================================
# ERROR LOGGING
# =============================================================================

async def log_error_to_api(
    tool_name: str,
    error_type: str,
    error_message: str,
    request_data: dict = None
) -> None:
    """
    Log error to database via API endpoint.
    Fire-and-forget - errors in logging are silently ignored.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{API_BASE_URL}/api/errors",
                json={
                    "source": "mcp_tool",
                    "tool_name": tool_name,
                    "error_type": error_type,
                    "error_message": error_message,
                    "request_data": request_data
                }
            )
    except Exception:
        pass  # Fire and forget - don't fail if logging fails


# =============================================================================
# MCP SERVER
# =============================================================================

server = Server("backtesting")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available backtesting tools"""
    return [
        Tool(
            name="list_strategies",
            description="""List all available trading strategies.

Returns strategies with name, description, type, parameters, and regime_filter.

Built-in strategies:
- MA Crossover: Trend-following (best for TREND_UP/DOWN)
- RSI Reversal: Mean-reversion (best for RANGE)
- Bollinger Bands: Volatility-based (best for RANGE)
- MACD Cross: Momentum (best for TREND_UP/DOWN)""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_strategy",
            description="""Get detailed information about a specific strategy.

Returns full strategy config including parameters, regime filters, and logic.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Strategy name (e.g., 'RSI Reversal')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="check_data",
            description="""Check if historical data is available for backtesting.

ALWAYS check before running backtest. Returns available date range.
If data missing, use fetch_data tool to download it.""",
            inputSchema={
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
                "required": ["symbol", "timeframe"]
            }
        ),
        Tool(
            name="fetch_data",
            description="""Fetch historical OHLCV data from Binance and store in database.

Use this when:
- User wants to test a symbol that doesn't have data
- check_data shows no data available

This may take a few seconds depending on date range.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair (e.g., 'BTCUSDT', 'BNBUSDC')"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
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
        ),
        Tool(
            name="run_backtest",
            description="""Run a backtest with a strategy on historical data.

PREREQUISITES: Strategy must exist, data must be available.

Returns:
- Metrics: total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor
- Trades: All trades with entry/exit prices and P&L
- Equity curve: Portfolio value over time

INTERPRETING RESULTS:
- Sharpe > 1.0 acceptable, > 2.0 good
- Win Rate > 50% with Profit Factor > 1.5 = edge
- Max Drawdown < 20% acceptable for crypto""",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy_name": {
                        "type": "string",
                        "description": "Name of strategy to test"
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
                        "description": "Only trade in these regimes: TREND_UP, TREND_DOWN, RANGE, CHOPPY, NEUTRAL"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Override strategy parameters"
                    }
                },
                "required": ["strategy_name", "start_date"]
            }
        ),
        Tool(
            name="create_strategy",
            description="""Create a new trading strategy (builtin variant or composite).

For builtin variant (recommended):
- Set builtin_class to one of: MovingAverageCrossover, RSIReversal, BollingerBands, MACDCross
- Set parameters to customize

For composite strategy:
- Define entry_logic and exit_logic as LogicTree JSON

REGIME RECOMMENDATIONS:
- TREND_UP/DOWN: MA Crossover, MACD Cross
- RANGE: RSI Reversal, Bollinger Bands
- CHOPPY: Avoid trading""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Unique strategy name"
                    },
                    "description": {
                        "type": "string"
                    },
                    "builtin_class": {
                        "type": "string",
                        "enum": ["MovingAverageCrossover", "RSIReversal", "BollingerBands", "MACDCross"],
                        "description": "Base strategy class for builtin variant"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Strategy parameters (e.g., {fast_period: 10, slow_period: 30})"
                    },
                    "entry_logic": {
                        "type": "object",
                        "description": "LogicTree for composite strategy entry"
                    },
                    "exit_logic": {
                        "type": "object",
                        "description": "LogicTree for composite strategy exit"
                    },
                    "regime_filter": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_market_regime",
            description="""Get current market regime classification for a symbol.

Returns regime data including:
- Simplified regime: TREND_UP, TREND_DOWN, RANGE, CHOPPY, NEUTRAL
- Full 3D regime: trend + volatility + momentum states
- Confidence score

Use this to decide which strategy type to use.""",
            inputSchema={
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
        ),
        Tool(
            name="get_data_stats",
            description="""Get statistics about all available data in the database.

Returns list of symbol/timeframe combinations with:
- Candle count
- First and last candle timestamps

Use this to see what data is available for backtesting.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="agent_chat",
            description="""Chat with the backtesting research agent.

The agent can help you:
- Design trading strategies based on market conditions
- Run backtests with proper validation
- Analyze results and provide recommendations
- Explain trading concepts and metrics

The agent maintains conversation context and guides you through a structured workflow:
1. Strategy Design - discuss and define trading approach
2. Strategy Validation - validate and register the strategy
3. Data Selection - choose appropriate historical data
4. Backtest Execution - run the backtest
5. Results Analysis - interpret results and get recommendations

Use conversation_id to continue an existing conversation.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Your message to the agent"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Optional conversation ID to continue existing chat"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="list_reports",
            description="""List saved backtest reports.

Returns recent backtest reports with:
- Strategy name and parameters
- Performance metrics (return, Sharpe, trades)
- Date range and symbol

Use get_report with report_id for full details.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of reports to return",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_report",
            description="""Get full details of a saved backtest report.

Returns complete report including:
- All performance metrics
- Equity curve data
- Trade history
- AI analysis and recommendations""",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "string",
                        "description": "UUID of the report"
                    }
                },
                "required": ["report_id"]
            }
        ),
        Tool(
            name="list_suggestions",
            description="""List feature suggestions made by the agent.

Returns suggestions for tool improvements organized by:
- Category (indicator, metric, visualization, etc.)
- Status (pending, planned, done)

Useful to see what enhancements have been identified.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planned", "in_progress", "done", "rejected"],
                        "description": "Filter by status"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_errors",
            description="""List recent error logs from the backtesting system.

Returns errors with:
- Error type and message
- Tool that caused the error
- Request data that triggered it
- Timestamp

Use this to diagnose issues with backtests or strategy creation.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "default": 20,
                        "description": "Max errors to return"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Filter by tool (e.g., 'run_backtest')"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a backtesting tool"""
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# =============================================================================
# TOOL EXECUTION
# =============================================================================

async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by calling the corresponding API endpoint."""

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            if tool_name == "list_strategies":
                response = await client.get(f"{API_BASE_URL}/api/strategies")

            elif tool_name == "get_strategy":
                name = arguments["name"]
                # URL encode the name to handle special characters like spaces and slashes
                encoded_name = quote(name, safe='')
                response = await client.get(f"{API_BASE_URL}/api/strategies/{encoded_name}")

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

            elif tool_name == "run_backtest":
                response = await client.post(
                    f"{API_BASE_URL}/api/backtest",
                    json=arguments
                )

            elif tool_name == "create_strategy":
                response = await client.post(
                    f"{API_BASE_URL}/api/strategies",
                    json=arguments
                )

            elif tool_name == "get_market_regime":
                symbol = arguments.get("symbol", "BTCUSDT")
                timeframe = arguments.get("timeframe", "1h")
                response = await client.get(
                    f"{API_BASE_URL}/api/data/regime/{symbol}/{timeframe}"
                )
                # Return only last 10 regime entries for brevity
                data = response.json()
                if isinstance(data, list) and len(data) > 10:
                    return {
                        "latest_regimes": data[-10:],
                        "total_entries": len(data),
                        "current_regime": data[-1] if data else None
                    }
                return data

            elif tool_name == "get_data_stats":
                response = await client.get(f"{API_BASE_URL}/api/data/stats")

            elif tool_name == "fetch_data":
                from datetime import datetime, timedelta
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

            elif tool_name == "agent_chat":
                response = await client.post(
                    f"{API_BASE_URL}/api/agent/chat",
                    json={
                        "message": arguments["message"],
                        "conversation_id": arguments.get("conversation_id")
                    },
                    timeout=180.0  # Agent may take longer
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

            elif tool_name == "list_suggestions":
                params = {}
                if "status" in arguments:
                    params["status"] = arguments["status"]
                response = await client.get(
                    f"{API_BASE_URL}/api/suggestions",
                    params=params
                )

            elif tool_name == "list_errors":
                params = {"limit": arguments.get("limit", 20)}
                if "tool_name" in arguments:
                    params["tool_name"] = arguments["tool_name"]
                response = await client.get(
                    f"{API_BASE_URL}/api/errors",
                    params=params
                )

            else:
                return {"error": f"Unknown tool: {tool_name}"}

            if response.status_code >= 400:
                error_detail = "Unknown error"
                try:
                    error_detail = response.json().get("detail", error_detail)
                except:
                    error_detail = response.text
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "detail": error_detail
                }

            return response.json()

        except httpx.ConnectError:
            # Log connection error (can't use API, so just try - it will fail silently)
            asyncio.create_task(log_error_to_api(
                tool_name=tool_name,
                error_type="ConnectError",
                error_message="Cannot connect to API server. Make sure FastAPI is running on localhost:8000",
                request_data=arguments
            ))
            return {
                "error": True,
                "detail": "Cannot connect to API server. Make sure FastAPI is running on localhost:8000"
            }
        except httpx.TimeoutException:
            # Log timeout error
            asyncio.create_task(log_error_to_api(
                tool_name=tool_name,
                error_type="TimeoutException",
                error_message="API request timed out",
                request_data=arguments
            ))
            return {
                "error": True,
                "detail": "API request timed out"
            }


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
