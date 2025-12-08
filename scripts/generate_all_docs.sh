#!/bin/bash
# Generate all auto-documentation files
# Run this before committing major changes or starting a new AI session

set -e  # Exit on error

echo "========================================="
echo "Generating Auto-Documentation"
echo "========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "→ Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠ No virtual environment found (venv/). Using system Python."
fi

echo ""
echo "-----------------------------------------"
echo "1. Generating API Documentation"
echo "-----------------------------------------"
python3 scripts/generate_api_docs.py
echo ""

echo "-----------------------------------------"
echo "2. Generating Database Schema"
echo "-----------------------------------------"
python3 scripts/generate_db_schema.py
echo ""

# Future: Add generate_types.py when implemented
# echo "-----------------------------------------"
# echo "3. Generating TypeScript Types"
# echo "-----------------------------------------"
# python3 scripts/generate_types.py
# echo ""

echo "========================================="
echo "✓ All Documentation Generated!"
echo "========================================="
echo ""
echo "Output location: Backtesting_Obsidian/05-Reference/_GENERATED/"
echo ""
echo "Next steps:"
echo "  1. Review generated files"
echo "  2. Commit to git if changes are significant"
echo "  3. Reference in your AI session"
echo ""
