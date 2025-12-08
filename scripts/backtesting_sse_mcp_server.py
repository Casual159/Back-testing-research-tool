#!/usr/bin/env python3
"""
SSE MCP Server for Backtesting Research Tool
Implements Model Context Protocol over Server-Sent Events (HTTP)
Runs on localhost and accessible from Langflow Docker via host.docker.internal
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import json
from typing import Any, Dict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Docker

# Tool implementations
def get_data_stats() -> Dict[str, Any]:
    """Get statistics about available data in the database"""
    try:
        response = requests.get(
            "http://localhost:8000/api/agent/tools/data-stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error in get_data_stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get data stats: {str(e)}"
        }


def fetch_candlestick_data(symbol: str, timeframe: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch historical OHLCV candlestick data from Binance"""
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
        logger.error(f"Error in fetch_candlestick_data: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch data: {str(e)}"
        }


# MCP endpoints
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "Backtesting MCP Server"})


@app.route('/sse', methods=['GET'])
def sse_endpoint():
    """SSE endpoint for MCP protocol"""
    def event_stream():
        # Send server info on connection
        yield f"data: {json.dumps({'type': 'server_info', 'name': 'Backtesting MCP Server', 'version': '1.0.0'})}\n\n"

        # Keep connection alive
        while True:
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            import time
            time.sleep(30)

    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/message', methods=['POST'])
def handle_message():
    """Handle MCP protocol messages"""
    try:
        data = request.json
        method = data.get("method")
        params = data.get("params", {})
        message_id = data.get("id")

        logger.info(f"Received method: {method}")

        if method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
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
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            logger.info(f"Calling tool: {tool_name} with args: {arguments}")

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
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }), 404

            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }

        else:
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": message_id if 'message_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500


if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Backtesting MCP Server (SSE)")
    print("=" * 80)
    print(f"🌐 Local URL:  http://localhost:9001")
    print(f"🐳 Docker URL: http://host.docker.internal:9001")
    print("📡 SSE endpoint: /sse")
    print("📨 Message endpoint: /message")
    print("=" * 80)

    # Install flask-cors if not available
    try:
        import flask_cors
    except ImportError:
        print("⚠️  Installing flask-cors...")
        import subprocess
        subprocess.check_call(["pip", "install", "flask-cors"])
        print("✅ flask-cors installed")

    app.run(host='0.0.0.0', port=9001, debug=False, threaded=True)
