#!/usr/bin/env python3
"""
Generate database schema documentation from PostgreSQL

Outputs SQL schema dump to Backtesting_Obsidian/05-Reference/_GENERATED/
"""
import sys
from pathlib import Path
from datetime import datetime
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Make sure dependencies are installed: pip install psycopg2-binary python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()


def get_db_config():
    """Get database configuration from environment"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'trading_bot'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }


def generate_db_schema():
    """Generate database schema documentation"""
    
    config = get_db_config()
    
    try:
        # Connect to database
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        output_lines = []
        output_lines.append(f"-- Auto-generated database schema documentation")
        output_lines.append(f"-- Generated: {datetime.now().isoformat()}")
        output_lines.append(f"-- Database: {config['database']}")
        output_lines.append(f"-- Host: {config['host']}:{config['port']}")
        output_lines.append("")
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        output_lines.append(f"-- Found {len(tables)} table(s)")
        output_lines.append("")
        
        for table in tables:
            output_lines.append("-" * 70)
            output_lines.append(f"-- Table: {table}")
            output_lines.append("-" * 70)
            output_lines.append("")
            
            # Get CREATE TABLE statement (reconstructed)
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            
            columns = cursor.fetchall()
            
            output_lines.append(f"CREATE TABLE {table} (")
            
            column_defs = []
            for col in columns:
                col_name, data_type, char_len, num_prec, num_scale, nullable, default = col
                
                # Build column type
                if data_type == 'character varying':
                    col_type = f"VARCHAR({char_len})" if char_len else "VARCHAR"
                elif data_type == 'numeric':
                    col_type = f"DECIMAL({num_prec},{num_scale})" if num_prec and num_scale else "DECIMAL"
                elif data_type == 'timestamp without time zone':
                    col_type = "TIMESTAMP"
                elif data_type == 'integer':
                    col_type = "INTEGER"
                else:
                    col_type = data_type.upper()
                
                # Build full definition
                col_def = f"    {col_name} {col_type}"
                
                if nullable == 'NO':
                    col_def += " NOT NULL"
                
                if default:
                    col_def += f" DEFAULT {default}"
                
                column_defs.append(col_def)
            
            output_lines.append(",\n".join(column_defs))
            
            # Get primary key
            cursor.execute("""
                SELECT 
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position;
            """, (table,))
            
            pk_columns = [row[0] for row in cursor.fetchall()]
            if pk_columns:
                output_lines.append(f",\n    PRIMARY KEY ({', '.join(pk_columns)})")
            
            output_lines.append(");")
            output_lines.append("")
            
            # Get indexes
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = %s
                AND indexname NOT LIKE '%_pkey'
                ORDER BY indexname;
            """, (table,))
            
            indexes = cursor.fetchall()
            if indexes:
                output_lines.append(f"-- Indexes for {table}")
                for idx_name, idx_def in indexes:
                    output_lines.append(f"{idx_def};")
                output_lines.append("")
            
            output_lines.append("")
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Write output
        output_dir = project_root / "Backtesting_Obsidian" / "05-Reference" / "_GENERATED"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "database_schema.sql"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"✓ Generated database schema documentation")
        print(f"  - Tables: {len(tables)}")
        print(f"  - Output: {output_file}")
        print(f"  - Generated: {datetime.now().isoformat()}")
        
        return output_file
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        print(f"  - Check your .env file has correct DB credentials")
        print(f"  - Ensure PostgreSQL is running")
        sys.exit(1)


if __name__ == "__main__":
    try:
        output_file = generate_db_schema()
        print(f"\n✓ Database schema successfully generated: {output_file}")
    except Exception as e:
        print(f"✗ Error generating database schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
