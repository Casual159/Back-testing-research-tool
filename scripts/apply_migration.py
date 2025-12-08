#!/usr/bin/env python3
"""
Apply database migrations
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import load_config
from core.data.storage import PostgresStorage

def apply_migration(migration_file: str):
    """Apply a SQL migration file to the database"""
    config = load_config()

    # Read migration file
    with open(migration_file, 'r') as f:
        sql = f.read()

    # Apply migration
    with PostgresStorage(config['database']) as storage:
        print(f"Applying migration: {migration_file}")
        storage.cursor.execute(sql)
        storage.conn.commit()
        print("✓ Migration applied successfully")

if __name__ == "__main__":
    migration_file = Path(__file__).parent.parent / "migrations" / "001_research_insights.sql"
    apply_migration(str(migration_file))
