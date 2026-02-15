"""
Monitoring and Error Analysis Tools

Provides tools for log analysis, error monitoring, and system health checks.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from anthropic import Anthropic


class MonitoringTools:
    """Monitoring and error analysis operations."""

    def __init__(
        self,
        api_base_url: str = os.getenv("API_BASE_URL", f"http://localhost:{os.getenv('PORT', '8000')}"),
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize monitoring tools.

        Args:
            api_base_url: Base URL for the API
            anthropic_api_key: Anthropic API key for AI analysis
        """
        self.api_base_url = api_base_url
        self.anthropic_client = None

        if anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=anthropic_api_key)

    async def fetch_errors(
        self, limit: int = 100, tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch recent errors from the error_logs table.

        Args:
            limit: Maximum number of errors to fetch
            tool_name: Filter by specific tool name

        Returns:
            Dict with error data
        """
        try:
            params = {"limit": limit}
            if tool_name:
                params["tool_name"] = tool_name

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_base_url}/api/errors", params=params)

                if response.status_code == 200:
                    errors = response.json()
                    return {"success": True, "errors": errors, "count": len(errors)}
                else:
                    return {
                        "success": False,
                        "error": f"API returned {response.status_code}: {response.text}",
                    }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_errors(self, errors: List[Dict]) -> Dict[str, Any]:
        """
        Analyze errors and identify patterns.

        Args:
            errors: List of error dictionaries

        Returns:
            Dict with analysis results
        """
        if not errors:
            return {"success": True, "message": "No errors to analyze", "analysis": {}}

        # Group errors by type
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "unknown")
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)

        # Count by tool
        tool_counts = {}
        for error in errors:
            tool = error.get("tool_name", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

        analysis = {
            "total_errors": len(errors),
            "error_types": {
                etype: len(errors) for etype, errors in error_types.items()
            },
            "tool_counts": tool_counts,
            "most_common_type": max(error_types.items(), key=lambda x: len(x[1]))[0]
            if error_types
            else None,
            "most_affected_tool": max(tool_counts.items(), key=lambda x: x[1])[0]
            if tool_counts
            else None,
        }

        return {"success": True, "analysis": analysis, "grouped_errors": error_types}

    async def ai_analyze_errors(self, errors: List[Dict]) -> Dict[str, Any]:
        """
        Use Claude to analyze errors and suggest fixes.

        Args:
            errors: List of error dictionaries

        Returns:
            Dict with AI analysis and recommendations
        """
        if not self.anthropic_client:
            return {
                "success": False,
                "error": "Anthropic API key not configured",
            }

        if not errors:
            return {
                "success": True,
                "message": "No errors to analyze",
                "recommendations": [],
            }

        # Prepare error summary for Claude
        error_summary = []
        for error in errors[:20]:  # Limit to 20 most recent
            error_summary.append(
                {
                    "type": error.get("error_type", "unknown"),
                    "message": error.get("error_message", ""),
                    "tool": error.get("tool_name", ""),
                    "timestamp": error.get("created_at", ""),
                }
            )

        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze these production errors and provide:
1. Root cause analysis
2. Severity assessment (critical/high/medium/low)
3. Specific fixes or improvements
4. Prevention strategies

Errors:
{error_summary}

Format your response as JSON with these fields:
- root_cause: string
- severity: string
- recommendations: array of strings
- prevention: array of strings
""",
                    }
                ],
            )

            # Parse Claude's response
            response_text = message.content[0].text

            # Try to extract JSON from response
            import json

            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: return raw text
                analysis = {
                    "root_cause": "See raw analysis",
                    "severity": "unknown",
                    "recommendations": [],
                    "prevention": [],
                    "raw_analysis": response_text,
                }

            return {"success": True, "ai_analysis": analysis}

        except Exception as e:
            return {"success": False, "error": f"AI analysis failed: {str(e)}"}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Dict with health status
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_base_url}/")

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "status": "healthy",
                        "service": data.get("service", "unknown"),
                        "version": data.get("version", "unknown"),
                    }
                else:
                    return {
                        "success": False,
                        "status": "unhealthy",
                        "error": f"API returned {response.status_code}",
                    }

        except Exception as e:
            return {
                "success": False,
                "status": "unreachable",
                "error": str(e),
            }

    async def get_data_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with data stats
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_base_url}/api/data/stats")

                if response.status_code == 200:
                    stats = response.json()
                    return {"success": True, "stats": stats}
                else:
                    return {
                        "success": False,
                        "error": f"API returned {response.status_code}: {response.text}",
                    }

        except Exception as e:
            return {"success": False, "error": str(e)}
