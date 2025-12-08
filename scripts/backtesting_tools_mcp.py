#!/usr/bin/env python3
"""
MCP Server for Backtesting Research Tool
Provides tools for data management and fetching
"""
import json
import sys
import requests
from typing import Any, Dict, List


def get_data_stats() -> Dict[str, Any]:
    """
    Get statistics about available data in the database.
    Returns information about all symbols, timeframes, candle counts, and date ranges.

    Returns:
        Dictionary with success status and data/error information
    """
    try:
        response = requests.get(
            "http://localhost:8000/api/agent/tools/data-stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get data stats: {str(e)}"
        }


def fetch_candlestick_data(symbol: str, timeframe: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Fetch historical OHLCV candlestick data from Binance and store in database.

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
        timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Dictionary with success status and data/error information
    """
    try:
        response = requests.post(
            "http://localhost:8000/api/agent/tools/fetch-data",
            json={
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch data: {str(e)}"
        }


# MCP Protocol Implementation
def handle_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP protocol messages"""
    method = message.get("method")
    params = message.get("params", {})

    if method == "tools/list":
        # Return available tools
        return {
            "tools": [
                {
                    "name": "get_data_stats",
                    "description": "Returns statistics about all available data in database including symbols, timeframes, candle counts and date ranges. No parameters needed.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "fetch_candlestick_data",
                    "description": "Fetches historical OHLCV data from Binance and stores in database. Agent MUST ask user for all 4 parameters before calling. Required: symbol (e.g. BTCUSDT), timeframe (e.g. 1h, 4h, 1d), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading pair (e.g., BTCUSDT, ETHUSDT)"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "Candle timeframe (e.g., 1h, 4h, 1d)"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format"
                            }
                        },
                        "required": ["symbol", "timeframe", "start_date", "end_date"]
                    }
                }
            ]
        }

    elif method == "tools/call":
        # Execute tool
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "get_data_stats":
            result = get_data_stats()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }

        elif tool_name == "fetch_candlestick_data":
            symbol = arguments.get("symbol")
            timeframe = arguments.get("timeframe")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")

            result = fetch_candlestick_data(symbol, timeframe, start_date, end_date)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }

        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

    else:
        return {
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}"
            }
        }


def main():
    """Main MCP server loop - reads from stdin, writes to stdout"""
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = handle_mcp_message(message)

            # Add id from request to response
            if "id" in message:
                response["id"] = message["id"]

            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
