"""
Agent Tools for Backtesting Research Tool

Defines Claude-compatible tool definitions for the trading agent.
These tools wrap the API endpoints and provide domain knowledge.
"""

# =============================================================================
# TOOL DEFINITIONS (Claude API format)
# =============================================================================

BACKTESTING_TOOLS = [
    {
        "name": "list_strategies",
        "description": """List all available trading strategies.

Returns a list of strategies with their:
- name: Strategy identifier
- description: What the strategy does
- strategy_type: 'builtin' (pre-defined) or 'composite' (user-created)
- parameters: Configurable settings
- regime_filter: Which market regimes this strategy is designed for

Built-in strategies include:
- MA Crossover: Trend-following using moving average crossovers
- RSI Reversal: Mean-reversion using RSI overbought/oversold
- Bollinger Bands: Volatility-based mean-reversion
- MACD Cross: Momentum strategy using MACD crossovers

Domain knowledge:
- Trend-following strategies (MA, MACD) work best in TREND_UP/TREND_DOWN regimes
- Mean-reversion strategies (RSI, BB) work best in RANGE regimes
- All strategies should avoid CHOPPY regimes""",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_strategy",
        "description": """Get detailed information about a specific strategy.

Returns full strategy details including:
- Entry/exit logic (for composite strategies)
- All parameters with current values
- Regime filter settings
- Creation date

Use this to understand how a strategy works before testing it.""",
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
        "description": """Check if historical data is available for backtesting.

IMPORTANT: Always check data availability before running a backtest.
Backtest = f(Strategy, Dataset) - both must exist.

Returns:
- available: true/false
- data_start, data_end: Available date range
- message: Helpful info about what to do if data is missing

If data is not available, instruct user to fetch it first.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')",
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
                    "description": "Start date in ISO format (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD)"
                }
            },
            "required": ["symbol", "timeframe"]
        }
    },
    {
        "name": "run_backtest",
        "description": """Run a backtest with a strategy on historical data.

PREREQUISITES:
1. Strategy must exist (check with list_strategies)
2. Data must be available (check with check_data)

Parameters:
- strategy_name: Must match an existing strategy name exactly
- symbol, timeframe, date range: Define the dataset
- regime_filter: Optional - only trade in specific regimes

Returns comprehensive results:
- Metrics: total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor
- trades: List of all trades with entry/exit prices and P&L
- equity_curve: Portfolio value over time

INTERPRETING RESULTS:
- Sharpe Ratio > 1.0 is acceptable, > 2.0 is good, > 3.0 is excellent
- Win Rate > 50% with Profit Factor > 1.5 indicates edge
- Max Drawdown < 20% is generally acceptable for crypto
- Total trades < 10 may not be statistically significant""",
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy_name": {
                    "type": "string",
                    "description": "Name of the strategy to test (must exist)"
                },
                "symbol": {
                    "type": "string",
                    "description": "Trading pair",
                    "default": "BTCUSDT"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1h", "4h", "1d"],
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
                },
                "initial_capital": {
                    "type": "number",
                    "description": "Starting capital in USD",
                    "default": 10000
                },
                "regime_filter": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["TREND_UP", "TREND_DOWN", "RANGE", "CHOPPY", "NEUTRAL"]
                    },
                    "description": "Only trade in these market regimes"
                },
                "parameters": {
                    "type": "object",
                    "description": "Override strategy parameters for this run"
                }
            },
            "required": ["strategy_name", "start_date"]
        }
    },
    {
        "name": "create_strategy",
        "description": """Create a new composite trading strategy.

Allows creating custom strategies by combining indicators and conditions.

Entry/Exit Logic Structure:
{
  "operator": "AND" or "OR",
  "children": [
    {
      "signal": {
        "name": "signal_name",
        "indicator": "RSI" | "MACD" | "SMA" | "EMA" | "BB",
        "parameters": {"period": 14, ...},
        "condition": {"operator": "<", "value": 30}
      }
    }
  ]
}

Available Indicators:
- RSI: Relative Strength Index (period)
- MACD: Moving Average Convergence (fast, slow, signal)
- SMA/EMA: Moving Averages (period)
- BB: Bollinger Bands (period, num_std)

Condition Operators:
- Comparison: "<", ">", "<=", ">=", "==", "!="
- Crossovers: "cross_above", "cross_below"

RECOMMENDATION BY REGIME:
- TREND_UP/DOWN: Use trend-following (MACD cross, MA cross)
- RANGE: Use mean-reversion (RSI extremes, BB touches)
- CHOPPY: Avoid trading or use very tight conditions""",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique strategy name"
                },
                "description": {
                    "type": "string",
                    "description": "What this strategy does"
                },
                "entry_logic": {
                    "type": "object",
                    "description": "LogicTree for entry conditions"
                },
                "exit_logic": {
                    "type": "object",
                    "description": "LogicTree for exit conditions"
                },
                "regime_filter": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["TREND_UP", "TREND_DOWN", "RANGE", "CHOPPY", "NEUTRAL"]
                    },
                    "description": "Only trade in these regimes"
                }
            },
            "required": ["name", "entry_logic", "exit_logic"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION (API Wrapper)
# =============================================================================

import httpx
from typing import Any, Dict, Optional

API_BASE_URL = "http://localhost:8000"


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by calling the corresponding API endpoint.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments

    Returns:
        API response as dictionary
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        if tool_name == "list_strategies":
            response = await client.get(f"{API_BASE_URL}/api/strategies")

        elif tool_name == "get_strategy":
            name = arguments["name"]
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

        else:
            return {"error": f"Unknown tool: {tool_name}"}

        if response.status_code >= 400:
            return {
                "error": True,
                "status_code": response.status_code,
                "detail": response.json().get("detail", "Unknown error")
            }

        return response.json()


# =============================================================================
# DOMAIN KNOWLEDGE (for agent reasoning)
# =============================================================================

STRATEGY_RECOMMENDATIONS = {
    "TREND_UP": {
        "recommended": ["MA Crossover", "MACD Cross"],
        "avoid": ["RSI Reversal"],
        "reason": "Trend-following strategies capture sustained upward movements"
    },
    "TREND_DOWN": {
        "recommended": ["MA Crossover", "MACD Cross"],
        "note": "These strategies can short or stay out in downtrends",
        "avoid": ["RSI Reversal"],
        "reason": "Mean-reversion can catch falling knives in strong downtrends"
    },
    "RANGE": {
        "recommended": ["RSI Reversal", "Bollinger Bands"],
        "avoid": ["MA Crossover"],
        "reason": "Mean-reversion works well when price oscillates in a range"
    },
    "CHOPPY": {
        "recommended": [],
        "avoid": ["all"],
        "reason": "High whipsaw risk - better to stay out"
    },
    "NEUTRAL": {
        "recommended": ["RSI Reversal", "Bollinger Bands"],
        "reason": "Low volatility suits mean-reversion with tight stops"
    }
}


def get_strategy_recommendation(regime: str) -> Dict[str, Any]:
    """Get strategy recommendations for a market regime"""
    return STRATEGY_RECOMMENDATIONS.get(regime, {
        "recommended": [],
        "reason": "Unknown regime"
    })


METRIC_INTERPRETATION = {
    "sharpe_ratio": {
        "< 0": "Losing money adjusted for risk - bad",
        "0-1": "Positive but not great risk-adjusted returns",
        "1-2": "Good risk-adjusted returns",
        "2-3": "Very good risk-adjusted returns",
        "> 3": "Excellent - but verify not overfitting"
    },
    "win_rate": {
        "< 40%": "Low - needs high profit factor to compensate",
        "40-50%": "Average - common for trend-following",
        "50-60%": "Good",
        "> 60%": "High - typical for mean-reversion with tight stops"
    },
    "max_drawdown": {
        "< 10%": "Excellent risk control",
        "10-20%": "Acceptable for crypto",
        "20-30%": "High but manageable",
        "> 30%": "Significant - may need position sizing adjustment"
    },
    "profit_factor": {
        "< 1": "Losing strategy",
        "1-1.5": "Marginal edge",
        "1.5-2": "Good edge",
        "> 2": "Strong edge"
    }
}


def interpret_metrics(metrics: Dict[str, float]) -> str:
    """Generate human-readable interpretation of backtest metrics"""
    interpretations = []

    sharpe = metrics.get("sharpe_ratio", 0)
    if sharpe < 0:
        interpretations.append(f"Sharpe {sharpe:.2f}: Losing money adjusted for risk")
    elif sharpe < 1:
        interpretations.append(f"Sharpe {sharpe:.2f}: Positive but modest risk-adjusted returns")
    elif sharpe < 2:
        interpretations.append(f"Sharpe {sharpe:.2f}: Good risk-adjusted returns")
    else:
        interpretations.append(f"Sharpe {sharpe:.2f}: Excellent risk-adjusted returns")

    win_rate = metrics.get("win_rate_pct", 0)
    pf = metrics.get("profit_factor", 0)
    if win_rate > 50 and pf > 1.5:
        interpretations.append(f"Win rate {win_rate:.1f}% with profit factor {pf:.2f} shows edge")
    elif pf > 1:
        interpretations.append(f"Profit factor {pf:.2f} indicates slight edge")
    else:
        interpretations.append(f"Profit factor {pf:.2f} - no clear edge")

    dd = abs(metrics.get("max_drawdown_pct", 0))
    if dd < 15:
        interpretations.append(f"Max DD {dd:.1f}%: Good risk control")
    elif dd < 25:
        interpretations.append(f"Max DD {dd:.1f}%: Acceptable for crypto")
    else:
        interpretations.append(f"Max DD {dd:.1f}%: High - consider smaller position sizes")

    return " | ".join(interpretations)
