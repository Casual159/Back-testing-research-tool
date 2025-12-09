#!/usr/bin/env python3
"""
Run database migration script
"""
import sys
sys.path.insert(0, '/Users/jakub/Back-testing-research-tool')

import psycopg2
from config.config import load_config

def run_migration(migration_file: str):
    """Run SQL migration file"""
    config = load_config()
    db_config = config['database']

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql = f.read()

    # Connect and execute
    conn = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password']
    )

    try:
        with conn.cursor() as cur:
            print(f"Running migration: {migration_file}")
            print("=" * 70)

            # Execute migration
            cur.execute(sql)
            conn.commit()

            print("✓ Migration completed successfully!")
            print()

            # Verify table creation
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'market_regimes'
                ORDER BY ordinal_position
            """)

            print("Table structure:")
            print("-" * 70)
            for row in cur.fetchall():
                print(f"  {row[0]:<30} {row[1]}")
            print()

            # Check indexes
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'market_regimes'
                ORDER BY indexname
            """)

            print("Indexes created:")
            print("-" * 70)
            for row in cur.fetchall():
                print(f"  {row[0]}")
            print()

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        sys.exit(1)

    migration_file = sys.argv[1]
    run_migration(migration_file)
