# src/core/config/validator.py

"""Schema validation for configuration.

This module provides functionality for validating configuration against
JSON schemas. It includes a SchemaValidator class that loads schema
definitions from JSON files and validates configuration dictionaries.
"""

import json
import logging
import jsonschema
import importlib.util
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path


class SchemaValidator:
    """Validates configuration against JSON schemas."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the schema validator.

        Args:
            logger: Optional logger instance.
        """
        self.logger = logger or logging.getLogger("core.config.validator")
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Any]:
        """Load all JSON schemas from the schemas directory.

        Returns:
            Dict mapping schema names to schema definitions.
        """
        schemas: Dict[str, Any] = {}
        schema_dir = Path(__file__).parent / "schemas"

        # Try to load schema modules
        for schema_name in ["core", "aws", "azure", "kubernetes"]:
            schema_module_path = schema_dir / f"{schema_name}_schema.py"
            schema_data = self._load_schema(schema_name, schema_module_path)
            if schema_data:
                schemas[schema_name] = schema_data

        if not schemas:
            self.logger.warning("No schemas were loaded. Schema validation will be skipped.")

        return schemas

    def _load_schema(self, schema_name: str, schema_module_path: Path) \
            -> Optional[Dict[str, Any]]:
        """Load a schema definition from a Python module or JSON file.

        Args:
            schema_name: Name of the schema to load
            schema_module_path: Path to the schema module

        Returns:
            Schema definition dictionary if loaded successfully, None otherwise
        """
        try:
            # Try to load from direct import first
            try:
                # Construct the proper module path
                from src.core.config.schemas import (
                    core_schema,
                    aws_schema,
                    azure_schema,
                    kubernetes_schema
                )
                
                schema_modules = {
                    "core": core_schema,
                    "aws": aws_schema,
                    "azure": azure_schema,
                    "kubernetes": kubernetes_schema
                }
                
                if schema_name in schema_modules:
                    return getattr(schema_modules[schema_name], "SCHEMA_DEFINITION")
            except (ImportError, AttributeError) as e:
                self.logger.debug(
                    f"Could not load schema from direct import {schema_name}: {str(e)}"
                )

            # Fall back to dynamic import
            try:
                module_spec = importlib.util.spec_from_file_location(
                    f"{schema_name}_schema", schema_module_path
                )
                if module_spec and module_spec.loader:
                    module = importlib.util.module_from_spec(module_spec)
                    module_spec.loader.exec_module(module)
                    return getattr(module, "SCHEMA_DEFINITION")
            except (ImportError, AttributeError) as e:
                self.logger.debug(
                    f"Could not load schema from file {schema_module_path}: {str(e)}"
                )

            # Fall back to JSON file if it exists
            json_path = schema_module_path.with_suffix(".json")
            if json_path.exists():
                with open(json_path, "r") as f:
                    return json.load(f)

            self.logger.warning(f"Schema definition not found: {schema_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error loading schema {schema_name}: {str(e)}")
            return None

    def validate(self, config: Dict[str, Any], schema_name: str) -> Tuple[bool, List[str]]:
        """Validate configuration against a named schema.

        Args:
            config: Configuration dictionary to validate
            schema_name: Name of the schema to validate against

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if schema_name not in self.schemas:
            self.logger.warning(f"Unknown schema: {schema_name}. Validation will be skipped.")
            return True, []

        schema = self.schemas[schema_name]
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(config))

        if not errors:
            return True, []

        # Format error messages
        error_messages = []
        for error in errors:
            path = "." .join(str(p) for p in error.path) if error.path else "root"
            message = f"{path}: {error.message}"
            error_messages.append(message)

        return False, error_messages

    def validate_provider_config(self, provider_type: str, config: Dict[str, Any]) \
            -> Tuple[bool, List[str]]:
        """Validate provider-specific configuration.

        Args:
            provider_type: The type of provider (e.g., 'aws', 'azure', 'kubernetes')
            config: Provider configuration to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self.validate(config, provider_type)