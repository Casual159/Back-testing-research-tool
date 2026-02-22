"""
Database Management Tools

Provides tools for database migrations, backups, and management.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class DatabaseTools:
    """Database management operations."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize database tools.

        Args:
            project_root: Path to project root (defaults to current directory parent)
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent

    def _run_alembic(self, args: List[str]) -> Dict:
        """
        Run Alembic command.

        Args:
            args: Alembic command arguments

        Returns:
            Dict with result
        """
        try:
            result = subprocess.run(
                ["alembic"] + args,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=120,
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
                "error": "Alembic command timed out after 120 seconds",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error": "Alembic not found. Install with: pip install alembic",
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    def upgrade(self, revision: str = "head") -> Dict:
        """
        Run database migrations up to a specific revision.

        Args:
            revision: Target revision (default: 'head' for latest)

        Returns:
            Dict with migration result
        """
        return self._run_alembic(["upgrade", revision])

    def downgrade(self, revision: str = "-1") -> Dict:
        """
        Downgrade database to a specific revision.

        Args:
            revision: Target revision (default: '-1' for previous)

        Returns:
            Dict with downgrade result
        """
        return self._run_alembic(["downgrade", revision])

    def current(self) -> Dict:
        """
        Show current database revision.

        Returns:
            Dict with current revision info
        """
        return self._run_alembic(["current"])

    def history(self, verbose: bool = False) -> Dict:
        """
        Show migration history.

        Args:
            verbose: Show detailed info

        Returns:
            Dict with migration history
        """
        args = ["history"]
        if verbose:
            args.append("--verbose")

        return self._run_alembic(args)

    def create_revision(self, message: str, autogenerate: bool = True) -> Dict:
        """
        Create a new migration revision.

        Args:
            message: Migration message
            autogenerate: Auto-detect changes from models

        Returns:
            Dict with result
        """
        args = ["revision", "-m", message]
        if autogenerate:
            args.append("--autogenerate")

        return self._run_alembic(args)

    def backup_database(self, database_url: str, backup_dir: Optional[Path] = None) -> Dict:
        """
        Create database backup using pg_dump.

        Args:
            database_url: PostgreSQL connection URL
            backup_dir: Directory to store backups (default: project_root/backups)

        Returns:
            Dict with backup info
        """
        if backup_dir is None:
            backup_dir = self.project_root / "backups"

        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.sql"

        try:
            result = subprocess.run(
                ["pg_dump", database_url, "-f", str(backup_file)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "backup_file": str(backup_file),
                    "timestamp": timestamp,
                    "message": f"Backup created: {backup_file}",
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip() if result.stderr else "pg_dump failed",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Backup timed out after 5 minutes",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "pg_dump not found. Install PostgreSQL client tools.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_database(self, database_url: str, backup_file: Path) -> Dict:
        """
        Restore database from backup.

        Args:
            database_url: PostgreSQL connection URL
            backup_file: Path to backup file

        Returns:
            Dict with restore result
        """
        if not backup_file.exists():
            return {"success": False, "error": f"Backup file not found: {backup_file}"}

        try:
            result = subprocess.run(
                ["psql", database_url, "-f", str(backup_file)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Database restored from {backup_file}",
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip() if result.stderr else "psql failed",
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Restore timed out after 5 minutes",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "psql not found. Install PostgreSQL client tools.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_pending_migrations(self) -> Dict:
        """
        Check if there are pending migrations.

        Returns:
            Dict with pending migration info
        """
        current = self._run_alembic(["current"])
        heads = self._run_alembic(["heads"])

        return {
            "current": current.get("output", ""),
            "heads": heads.get("output", ""),
            "has_pending": current.get("output", "") != heads.get("output", ""),
        }
