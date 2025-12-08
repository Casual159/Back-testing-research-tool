#!/usr/bin/env python3
"""
Generate API documentation from FastAPI application

Outputs OpenAPI schema as JSON to Backtesting_Obsidian/05-Reference/_GENERATED/
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from api.main import app
    from fastapi.openapi.utils import get_openapi
except ImportError as e:
    print(f"Error importing FastAPI app: {e}")
    print("Make sure FastAPI is installed: pip install fastapi")
    sys.exit(1)


def generate_api_docs():
    """Generate OpenAPI schema from FastAPI app"""
    
    # Get OpenAPI schema
    schema = get_openapi(
        title=app.title or "Backtesting API",
        version=app.version or "1.0.0",
        openapi_version="3.1.0",
        description=app.description or "API for Backtesting Research Tool",
        routes=app.routes,
    )
    
    # Add generation metadata
    schema["info"]["x-generated-at"] = datetime.now().isoformat()
    schema["info"]["x-generator"] = "scripts/generate_api_docs.py"
    
    # Output path
    output_dir = project_root / "Backtesting_Obsidian" / "05-Reference" / "_GENERATED"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "api_endpoints.json"
    
    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    # Count endpoints
    endpoint_count = len(schema.get("paths", {}))
    
    print(f"✓ Generated API documentation")
    print(f"  - Endpoints: {endpoint_count}")
    print(f"  - Output: {output_file}")
    print(f"  - Generated: {schema['info']['x-generated-at']}")
    
    return output_file


if __name__ == "__main__":
    try:
        output_file = generate_api_docs()
        print(f"\n✓ API docs successfully generated: {output_file}")
    except Exception as e:
        print(f"✗ Error generating API docs: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
