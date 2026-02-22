"""
DevOps MCP Server for Railway Deployment Automation

Exposes DevOps tools via Model Context Protocol for Claude Code integration.
"""

import asyncio
import json
import os
import subprocess
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
        # =================================================================
        # PIPELINE & ENVIRONMENT TOOLS
        # =================================================================
        Tool(
            name="env_diff",
            description="""Compare environment variables between two Railway environments.

Shows variables that differ, are missing, or have different values.
Useful before promoting staging to production.

Returns:
- Variables only in env_a
- Variables only in env_b
- Variables with different values
- Variables that match (count only)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "env_a": {
                        "type": "string",
                        "description": "First environment name (default: TestEnv)",
                        "default": "TestEnv",
                    },
                    "env_b": {
                        "type": "string",
                        "description": "Second environment name (default: Production)",
                        "default": "Production",
                    },
                },
            },
        ),
        Tool(
            name="pre_deploy_check",
            description="""Run pre-deployment validation checks.

Checks:
1. Pending database migrations
2. Frontend build (npm run build)
3. Python syntax check (py_compile on api/main.py)

Returns pass/fail for each check. Run this BEFORE deploying.

Args:
- skip_build: Skip the frontend build check (faster, default: false)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "skip_build": {
                        "type": "boolean",
                        "description": "Skip frontend build check",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="promote",
            description="""Promote staging deployment to production.

WORKFLOW:
1. Runs pre_deploy_check
2. Deploys to Production environment
3. Waits for deployment to start
4. Returns deployment info

Use railway_logs to monitor progress after promotion.

IMPORTANT: Ensure staging has been tested first!""",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="rollback",
            description="""Rollback to the previous deployment on an environment.

Uses Railway's built-in rollback to revert to the last successful deployment.

Args:
- environment: Environment to rollback (default: Production)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Environment to rollback (default: Production)",
                        "default": "Production",
                    },
                },
            },
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

        # PIPELINE & ENVIRONMENT TOOLS
        elif tool_name == "env_diff":
            env_a = arguments.get("env_a", "TestEnv")
            env_b = arguments.get("env_b", "Production")
            return _env_diff(env_a, env_b)

        elif tool_name == "pre_deploy_check":
            skip_build = arguments.get("skip_build", False)
            return await _pre_deploy_check(skip_build=skip_build)

        elif tool_name == "promote":
            return await _promote()

        elif tool_name == "rollback":
            environment = arguments.get("environment", "Production")
            return _rollback(environment)

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
# PIPELINE & ENVIRONMENT HELPERS
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent


def _env_diff(env_a: str, env_b: str) -> dict[str, Any]:
    """Compare environment variables between two Railway environments."""
    vars_a = railway.get_variables(environment=env_a)
    vars_b = railway.get_variables(environment=env_b)

    if not vars_a.get("success"):
        return {"error": f"Failed to get variables for {env_a}: {vars_a.get('error')}"}
    if not vars_b.get("success"):
        return {"error": f"Failed to get variables for {env_b}: {vars_b.get('error')}"}

    data_a = vars_a.get("data", {})
    data_b = vars_b.get("data", {})

    keys_a = set(data_a.keys())
    keys_b = set(data_b.keys())

    only_a = sorted(keys_a - keys_b)
    only_b = sorted(keys_b - keys_a)
    common = keys_a & keys_b

    different = {}
    matching = 0
    for key in sorted(common):
        if data_a[key] != data_b[key]:
            # Mask sensitive values
            sensitive = any(s in key.upper() for s in ["SECRET", "PASSWORD", "KEY", "TOKEN"])
            if sensitive:
                different[key] = {env_a: "***", env_b: "***", "note": "values differ (masked)"}
            else:
                different[key] = {env_a: data_a[key], env_b: data_b[key]}
        else:
            matching += 1

    return {
        "success": True,
        "env_a": env_a,
        "env_b": env_b,
        f"only_in_{env_a}": only_a,
        f"only_in_{env_b}": only_b,
        "different_values": different,
        "matching_count": matching,
    }


async def _pre_deploy_check(skip_build: bool = False) -> dict[str, Any]:
    """Run pre-deployment validation checks."""
    checks: dict[str, Any] = {}

    # 1. Pending migrations
    migration_result = database.check_pending_migrations()
    checks["migrations"] = {
        "passed": not migration_result.get("has_pending", True),
        "current": migration_result.get("current", "unknown"),
        "heads": migration_result.get("heads", "unknown"),
    }

    # 2. Python syntax check
    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", str(PROJECT_ROOT / "api" / "main.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        checks["python_syntax"] = {
            "passed": result.returncode == 0,
            "error": result.stderr.strip() if result.returncode != 0 else None,
        }
    except Exception as e:
        checks["python_syntax"] = {"passed": False, "error": str(e)}

    # 3. Frontend build
    if skip_build:
        checks["frontend_build"] = {"passed": True, "skipped": True}
    else:
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT / "frontend",
                timeout=120,
            )
            checks["frontend_build"] = {
                "passed": result.returncode == 0,
                "error": result.stderr.strip()[-500:] if result.returncode != 0 else None,
            }
        except Exception as e:
            checks["frontend_build"] = {"passed": False, "error": str(e)}

    all_passed = all(c["passed"] for c in checks.values())
    return {"success": True, "all_passed": all_passed, "checks": checks}


async def _promote() -> dict[str, Any]:
    """Promote staging to production."""
    # 1. Run pre-deploy checks (skip build — Railway builds on push)
    check_result = await _pre_deploy_check(skip_build=True)
    if not check_result.get("all_passed"):
        return {
            "success": False,
            "error": "Pre-deploy checks failed",
            "checks": check_result.get("checks", {}),
        }

    # 2. Deploy to Production
    deploy_result = railway.deploy(environment="Production", detach=True)

    return {
        "success": deploy_result.get("success", False),
        "pre_deploy_checks": check_result.get("checks", {}),
        "deployment": deploy_result,
        "message": "Deployment started. Use railway_logs to monitor progress."
        if deploy_result.get("success")
        else f"Deployment failed: {deploy_result.get('error')}",
    }


def _rollback(environment: str) -> dict[str, Any]:
    """Rollback to the previous deployment."""
    result = RailwayTools._run_command(["redeploy", "-e", environment, "--yes"])
    return {
        "success": result.get("success", False),
        "environment": environment,
        "output": result.get("output", ""),
        "error": result.get("error"),
        "message": f"Rollback initiated on {environment}"
        if result.get("success")
        else f"Rollback failed: {result.get('error')}",
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
