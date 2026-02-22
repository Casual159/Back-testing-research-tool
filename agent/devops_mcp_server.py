"""
DevOps MCP Server for Railway Deployment Automation

Exposes DevOps tools via Model Context Protocol for Claude Code integration.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tools.database_tools import DatabaseTools
from agent.tools.monitoring_tools import MonitoringTools
from agent.tools.railway_tools import RailwayTools

# =============================================================================
# CONFIGURATION
# =============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# =============================================================================
# TOOL INSTANCES
# =============================================================================

railway = RailwayTools()
database = DatabaseTools()
monitoring = MonitoringTools(
    api_base_url=API_BASE_URL,
    anthropic_api_key=ANTHROPIC_API_KEY,
)

# =============================================================================
# MCP SERVER
# =============================================================================

server = Server("devops")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available DevOps tools"""
    return [
        # =================================================================
        # RAILWAY DEPLOYMENT TOOLS
        # =================================================================
        Tool(
            name="railway_status",
            description="""Get deployment status for a Railway environment.

Returns current deployment information including:
- Deployment status (deployed, deploying, failed)
- Current version/commit
- Service health
- Domain URLs

Use this to check if services are running properly.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Environment name (staging, production). Optional.",
                    }
                },
            },
        ),
        Tool(
            name="railway_deploy",
            description="""Deploy to Railway environment.

WORKFLOW:
1. Checks current status
2. Triggers deployment
3. Returns deployment info

IMPORTANT: This starts a deployment. Use railway_logs to monitor progress.

Args:
- environment: staging or production
- detach: run in background (default: true)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Environment name (staging, production). Optional.",
                    },
                    "detach": {
                        "type": "boolean",
                        "description": "Run deployment in background",
                        "default": True,
                    },
                },
            },
        ),
        Tool(
            name="railway_logs",
            description="""Fetch deployment logs from Railway.

Use this to:
- Debug deployment issues
- Monitor application health
- Check for errors

Args:
- environment: Environment name
- lines: Number of lines (default: 100, max: 1000)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Environment name. Optional.",
                    },
                    "lines": {
                        "type": "number",
                        "description": "Number of log lines to fetch",
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="railway_list_environments",
            description="""List all Railway environments for this project.

Returns list of environments with:
- Environment name
- Service info
- Current deployment status""",
            inputSchema={"type": "object", "properties": {}},
        ),
        # =================================================================
        # DATABASE TOOLS
        # =================================================================
        Tool(
            name="db_migrate",
            description="""Run database migrations using Alembic.

CRITICAL: Always run on staging first before production!

Args:
- revision: Target revision (default: 'head' for latest)

Returns migration result including applied migrations.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "revision": {
                        "type": "string",
                        "description": "Target revision (default: head)",
                        "default": "head",
                    }
                },
            },
        ),
        Tool(
            name="db_current",
            description="""Show current database migration revision.

Use this to check what migrations are applied.""",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="db_history",
            description="""Show migration history.

Args:
- verbose: Show detailed migration info (default: false)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "verbose": {
                        "type": "boolean",
                        "description": "Show detailed info",
                        "default": False,
                    }
                },
            },
        ),
        Tool(
            name="db_check_pending",
            description="""Check if there are pending migrations.

Returns:
- Current revision
- Latest revision (head)
- Whether migrations are pending

IMPORTANT: Always check before deploying!""",
            inputSchema={"type": "object", "properties": {}},
        ),
        # =================================================================
        # MONITORING TOOLS
        # =================================================================
        Tool(
            name="monitor_health",
            description="""Check API health status.

Returns:
- Service status (healthy/unhealthy/unreachable)
- Version info
- Response time

Use this to verify deployments are working.""",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="monitor_errors",
            description="""Fetch recent errors from production.

Returns error logs with:
- Error type
- Error message
- Tool/endpoint that failed
- Timestamp

Args:
- limit: Max errors to fetch (default: 100)
- tool_name: Filter by specific tool (optional)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Max errors to return",
                        "default": 100,
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Filter by tool name",
                    },
                },
            },
        ),
        Tool(
            name="monitor_analyze_errors",
            description="""Analyze errors with AI to identify patterns and fixes.

REQUIRES: ANTHROPIC_API_KEY environment variable

This tool:
1. Fetches recent errors
2. Groups by type/tool
3. Uses Claude to analyze root cause
4. Suggests fixes and prevention strategies

Returns:
- Error patterns
- Root cause analysis
- Recommended fixes
- Prevention strategies

Args:
- limit: Number of errors to analyze (default: 100)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of errors to analyze",
                        "default": 100,
                    }
                },
            },
        ),
        Tool(
            name="monitor_data_stats",
            description="""Get database statistics.

Returns:
- Available symbols and timeframes
- Data ranges
- Storage info

Use this to verify data availability for backtesting.""",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a DevOps tool"""
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": str(e), "tool": name}, indent=2),
            )
        ]


# =============================================================================
# TOOL EXECUTION
# =============================================================================


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by calling the corresponding function."""

    try:
        # RAILWAY TOOLS
        if tool_name == "railway_status":
            environment = arguments.get("environment")
            return railway.status(environment=environment)

        elif tool_name == "railway_deploy":
            environment = arguments.get("environment")
            detach = arguments.get("detach", True)
            return railway.deploy(environment=environment, detach=detach)

        elif tool_name == "railway_logs":
            environment = arguments.get("environment")
            lines = arguments.get("lines", 100)
            return railway.logs(environment=environment, lines=lines)

        elif tool_name == "railway_list_environments":
            return railway.list_environments()

        # DATABASE TOOLS
        elif tool_name == "db_migrate":
            revision = arguments.get("revision", "head")
            return database.upgrade(revision=revision)

        elif tool_name == "db_current":
            return database.current()

        elif tool_name == "db_history":
            verbose = arguments.get("verbose", False)
            return database.history(verbose=verbose)

        elif tool_name == "db_check_pending":
            return database.check_pending_migrations()

        # MONITORING TOOLS
        elif tool_name == "monitor_health":
            return await monitoring.health_check()

        elif tool_name == "monitor_errors":
            limit = arguments.get("limit", 100)
            tool_name_filter = arguments.get("tool_name")
            return await monitoring.fetch_errors(limit=limit, tool_name=tool_name_filter)

        elif tool_name == "monitor_analyze_errors":
            limit = arguments.get("limit", 100)
            # Fetch errors first
            errors_result = await monitoring.fetch_errors(limit=limit)
            if not errors_result.get("success"):
                return errors_result

            errors = errors_result.get("errors", [])

            # Basic analysis
            basic_analysis = monitoring.analyze_errors(errors)

            # AI analysis (if configured)
            ai_analysis = await monitoring.ai_analyze_errors(errors)

            return {
                "success": True,
                "total_errors": len(errors),
                "basic_analysis": basic_analysis.get("analysis", {}),
                "ai_analysis": ai_analysis.get("ai_analysis", {}),
            }

        elif tool_name == "monitor_data_stats":
            return await monitoring.get_data_stats()

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {
            "error": True,
            "tool": tool_name,
            "message": str(e),
            "type": type(e).__name__,
        }


# =============================================================================
# MAIN
# =============================================================================


async def main():
    """Run the DevOps MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
