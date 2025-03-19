# src/core/config/schemas/__init__.py

"""Schema definitions for configuration validation.

This package contains JSON schema definitions for validating configuration 
data against expected structure and data types.
"""

from pathlib import Path
import json
from typing import Dict, Any


def load_schemas() -> Dict[str, Any]:
    """Load all available schema definitions.

    Returns:
        Dictionary mapping schema names to schema definitions.
    """
    schemas = {}
    schema_dir = Path(__file__).parent

    # Try to load schema modules or JSON files
    for schema_name in ["core", "aws", "azure", "kubernetes"]:
        module_name = f"{schema_name}_schema"
        
        # Look for the schema in a Python module first
        try:
            module = __import__(module_name, fromlist=["SCHEMA_DEFINITION"])
            schemas[schema_name] = getattr(module, "SCHEMA_DEFINITION")
            continue
        except (ImportError, AttributeError):
            pass

        # Try loading from a JSON file instead
        json_path = schema_dir / f"{module_name}.json"
        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    schemas[schema_name] = json.load(f)
            except json.JSONDecodeError:
                pass

    return schemas