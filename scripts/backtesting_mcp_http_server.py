#!/usr/bin/env python3
"""
HTTP MCP Server for Backtesting Research Tool
Runs as standalone HTTP server that Langflow can connect to from Docker
"""
from flask import Flask, request, jsonify
import requests
from typing import Any, Dict

app = Flask(__name__)

# Tool implementations
def get_data_stats() -> Dict[str, Any]:
    """Get statistics about available data in the database"""
    try:
        response = requests.get(
            "http://host.docker.internal:8000/api/agent/tools/data-stats",
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
    """Fetch historical OHLCV candlestick data from Binance"""
    try:
        response = requests.post(
            "http://host.docker.internal:8000/api/agent/tools/fetch-data",
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


# MCP Protocol endpoints
@app.route('/', methods=['GET'])
def root():
    """Root endpoint - MCP server info with tools"""
    return jsonify({
        "name": "Backtesting MCP Server",
        "version": "1.0.0",
        "protocol": "mcp",
        "capabilities": {
            "tools": True
        },
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
    })


@app.route('/tools/list', methods=['POST'])
def list_tools():
    """List available tools"""
    return jsonify({
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
    })


@app.route('/tools/call', methods=['POST'])
def call_tool():
    """Execute a tool"""
    data = request.json
    tool_name = data.get("name")
    arguments = data.get("arguments", {})

    if tool_name == "get_data_stats":
        result = get_data_stats()
    elif tool_name == "fetch_candlestick_data":
        symbol = arguments.get("symbol")
        timeframe = arguments.get("timeframe")
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        result = fetch_candlestick_data(symbol, timeframe, start_date, end_date)
    else:
        return jsonify({
            "error": {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
        }), 404

    return jsonify({
        "content": [
            {
                "type": "text",
                "text": str(result)
            }
        ]
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("🚀 Starting Backtesting MCP HTTP Server on http://localhost:9000")
    print("📡 Langflow can connect from Docker using: http://host.docker.internal:9000")
    app.run(host='0.0.0.0', port=9000, debug=False)
