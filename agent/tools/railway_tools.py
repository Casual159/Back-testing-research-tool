"""
Railway Deployment Tools

Provides wrapper around Railway CLI for deployment automation.
"""

import json
import subprocess
from typing import Dict, List, Optional


class RailwayTools:
    """Railway CLI wrapper for deployment operations."""

    @staticmethod
    def _run_command(args: List[str], capture_output: bool = True) -> Dict:
        """
        Run Railway CLI command and return result.

        Args:
            args: Command arguments (e.g., ['status', '--json'])
            capture_output: Whether to capture stdout/stderr

        Returns:
            Dict with 'success', 'output', and optionally 'error'
        """
        try:
            result = subprocess.run(
                ["railway"] + args,
                capture_output=capture_output,
                text=True,
                timeout=60,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip() if result.stdout else "",
                "error": result.stderr.strip() if result.stderr else None,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Command timed out after 60 seconds",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error": "Railway CLI not found. Install with: npm i -g @railway/cli",
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    @staticmethod
    def status(environment: Optional[str] = None) -> Dict:
        """
        Get deployment status for an environment.

        Args:
            environment: Environment name (staging, production, etc.)

        Returns:
            Dict with deployment status
        """
        args = ["status", "--json"]
        if environment:
            args.extend(["-e", environment])

        result = RailwayTools._run_command(args)

        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                pass

        return result

    @staticmethod
    def deploy(environment: Optional[str] = None, detach: bool = True) -> Dict:
        """
        Deploy to Railway.

        Args:
            environment: Environment name (staging, production, etc.)
            detach: Whether to run deployment in background

        Returns:
            Dict with deployment result
        """
        args = ["up"]
        if environment:
            args.extend(["-e", environment])
        if detach:
            args.append("--detach")

        return RailwayTools._run_command(args)

    @staticmethod
    def logs(
        environment: Optional[str] = None, lines: int = 100, follow: bool = False
    ) -> Dict:
        """
        Fetch deployment logs.

        Args:
            environment: Environment name
            lines: Number of lines to fetch
            follow: Whether to stream logs (not recommended for MCP)

        Returns:
            Dict with logs
        """
        args = ["logs"]
        if environment:
            args.extend(["-e", environment])
        if lines:
            args.extend(["--lines", str(lines)])
        if follow:
            args.append("--follow")

        return RailwayTools._run_command(args)

    @staticmethod
    def list_environments() -> Dict:
        """
        List all available environments.

        Returns:
            Dict with environment list
        """
        result = RailwayTools._run_command(["environment", "list", "--json"])

        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                pass

        return result

    @staticmethod
    def link_project(project_id: Optional[str] = None) -> Dict:
        """
        Link current directory to Railway project.

        Args:
            project_id: Optional project ID to link to

        Returns:
            Dict with link result
        """
        args = ["link"]
        if project_id:
            args.append(project_id)

        return RailwayTools._run_command(args)

    @staticmethod
    def run_command(command: str, environment: Optional[str] = None) -> Dict:
        """
        Run a command in Railway environment (e.g., migrations).

        Args:
            command: Command to run (e.g., "alembic upgrade head")
            environment: Environment name

        Returns:
            Dict with command result
        """
        args = ["run"]
        if environment:
            args.extend(["-e", environment])
        args.append(command)

        return RailwayTools._run_command(args)

    @staticmethod
    def get_variables(environment: Optional[str] = None) -> Dict:
        """
        Get environment variables for an environment.

        Args:
            environment: Environment name

        Returns:
            Dict with environment variables
        """
        args = ["variables", "--json"]
        if environment:
            args.extend(["-e", environment])

        result = RailwayTools._run_command(args)

        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                pass

        return result

    @staticmethod
    def set_variable(key: str, value: str, environment: Optional[str] = None) -> Dict:
        """
        Set an environment variable.

        Args:
            key: Variable name
            value: Variable value
            environment: Environment name

        Returns:
            Dict with result
        """
        args = ["variables", "--set", f"{key}={value}"]
        if environment:
            args.extend(["-e", environment])

        return RailwayTools._run_command(args)

    @staticmethod
    def domain_list(environment: Optional[str] = None) -> Dict:
        """
        List domains for an environment.

        Args:
            environment: Environment name

        Returns:
            Dict with domain list
        """
        args = ["domain", "list", "--json"]
        if environment:
            args.extend(["-e", environment])

        result = RailwayTools._run_command(args)

        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                pass

        return result

    @staticmethod
    def whoami() -> Dict:
        """
        Get current Railway user info.

        Returns:
            Dict with user info
        """
        return RailwayTools._run_command(["whoami"])
