#!/usr/bin/env python3
"""
Quick script to test PostgreSQL connection and create database
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config.config import Config

def test_connection():
    """Test PostgreSQL connection and create database if needed"""

    # First, try to connect to postgres database (always exists)
    try:
        print(f"Trying to connect to PostgreSQL as user: {Config.POSTGRES_USER}")
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            database='postgres',  # Connect to default postgres database first
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD if Config.POSTGRES_PASSWORD else None
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("✅ Successfully connected to PostgreSQL!")

        # Check if trading_bot database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'trading_bot'")
        exists = cursor.fetchone()

        if exists:
            print("✅ Database 'trading_bot' already exists")
        else:
            print("Creating database 'trading_bot'...")
            cursor.execute("CREATE DATABASE trading_bot")
            print("✅ Database 'trading_bot' created successfully!")

        cursor.close()
        conn.close()

        # Now test connection to trading_bot database
        print("\nTesting connection to 'trading_bot' database...")
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            database=Config.POSTGRES_DB,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD if Config.POSTGRES_PASSWORD else None
        )

        print("✅ Successfully connected to 'trading_bot' database!")

        # Test creating tables
        from core.data.storage import PostgresStorage
        storage = PostgresStorage(Config.get_postgres_config())
        storage.connect()
        storage.create_tables()
        print("✅ Tables created successfully!")
        storage.disconnect()

        print("\n" + "="*50)
        print("🎉 PostgreSQL setup complete!")
        print("="*50)
        print(f"\nConnection details:")
        print(f"  Host: {Config.POSTGRES_HOST}")
        print(f"  Port: {Config.POSTGRES_PORT}")
        print(f"  Database: {Config.POSTGRES_DB}")
        print(f"  User: {Config.POSTGRES_USER}")

        conn.close()
        return True

    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nPossible solutions:")
        print("1. Check if PostgreSQL is running: brew services list")
        print("2. Verify username in .env file (should be your macOS username)")
        print("3. Try setting POSTGRES_PASSWORD in .env if needed")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
