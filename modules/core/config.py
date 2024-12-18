# ./modules/core/config.py

"""
Configuration Management Module

This module handles the retrieval and preparation of configurations for different modules
within the Pulumi IaC program. It centralizes configuration logic to promote reuse
and maintainability.

Key Functions:
- get_module_config: Retrieves and prepares module configuration.
- export_results: Exports global deployment stack metadata.

Includes proper data type handling to ensure configurations are correctly parsed.
"""


import json
import pulumi
import requests

from pulumi import log
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, List
from pydantic import ValidationError
from urllib.parse import urlparse


from .types import (
    InitializationConfig,
    ModuleDefaults,
    ModuleBase,
    StackOutputs,
)
from .types import ComplianceConfig

# Configuration Constants


# Default Cache Directory Path
CACHE_DIR = Path("/tmp/konductor")


# Local artifact read/write & caching directory
def ensure_cache_dir() -> None:
    """Ensures the cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


# Coerce a value to a boolean
def coerce_to_bool(value: Any) -> bool:
    """
    Coerces a value to a boolean.

    Args:
        value: The value to coerce.

    Returns:
        bool: The coerced boolean value.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def get_module_config(
    module_name: str,
    config: pulumi.Config,
) -> Tuple[Dict[str, Any], bool]:
    """
    Retrieves and prepares the configuration for a module.

    Args:
        module_name: The name of the module to configure
        config: The Pulumi configuration object

    Returns:
        A tuple containing:
            - Module's configuration dictionary
            - Boolean indicating if the module is enabled

    Raises:
        ValueError: If module configuration is invalid
    """
    try:
        # TODO: Implement dynamic module defaults loading via dynamic module discovery and loading.
        # module_defaults = DEFAULT_MODULE_CONFIG.get(module_name, ModuleDefaults(enabled=False, config={}))

        # Get module configuration from Pulumi config
        module_config: Dict[str, Any] = config.get_object(module_name) or {}

        # Determine if module is enabled
        # Prefer module_config.enabled over module_defaults.enabled, default to False if neither is set
        # enabled = coerce_to_bool(module_config.get("enabled", module_defaults["enabled"]), False)
        enabled = coerce_to_bool(module_config.get("enabled", False))

        return module_config, enabled

    except Exception as e:
        log.error(f"Error configuring module {module_name}: {str(e)}")
        raise


def export_results(
    configurations: Dict[str, Dict[str, Any]],
    compliance: ComplianceConfig,
) -> None:
    """
    Exports deployment results including configurations, and compliance information.

    Args:
        configurations: Configurations of deployed modules.
        compliance: Compliance configuration.
    """
    try:
        # Convert compliance to dictionary if it's a Pydantic model
        compliance_dict = compliance.dict() if isinstance(compliance, ComplianceConfig) else compliance

        # Export results
        pulumi.export("configuration", configurations)
        pulumi.export("compliance", compliance_dict)

    except Exception as e:
        log.error(f"Failed to export results: {str(e)}")
        raise


def validate_module_config(
    module_name: str,
    config: Dict[str, Any],
    module_class: Optional[type[ModuleBase]] = None,
) -> None:
    """
    Validates module configuration against its schema.

    Args:
        module_name: Name of the module.
        config: Module configuration to validate.
        module_class: Optional module configuration class.

    Raises:
        ValueError: If configuration is invalid.
    """
    try:
        # Validate basic structure
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Check required fields
        required_fields = {"enabled"}
        missing_fields = required_fields - set(config.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate with module class if provided
        if module_class:
            module_class(**config)

    except ValidationError as e:
        log.error(f"Invalid configuration for module {module_name}: {str(e)}")
        raise ValueError(f"Invalid configuration for module {module_name}: {str(e)}")
    except Exception as e:
        log.error(f"Configuration validation failed for {module_name}: {str(e)}")
        raise


def merge_configurations(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two configurations with override taking precedence.

    Args:
        base_config: Base configuration
        override_config: Override configuration

    Returns:
        Dict[str, Any]: Merged configuration
    """
    result = base_config.copy()
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configurations(result[key], value)
        else:
            result[key] = value
    return result


def initialize_config(stack_config: Dict[str, Any]) -> InitializationConfig:
    """
    Initializes core configuration from stack configuration.

    Args:
        stack_config: Stack configuration dictionary.

    Returns:
        InitializationConfig: Initialized configuration object.

    Raises:
        ValueError: If configuration is invalid.
    """
    try:
        # Validate stack config structure
        if not isinstance(stack_config, dict):
            raise ValueError("Stack configuration must be a dictionary")

        # Ensure required fields
        required_fields = {"project_name", "stack_name"}
        missing_fields = required_fields - set(stack_config.keys())
        if missing_fields:
            raise ValueError(f"Missing required stack configuration fields: {missing_fields}")

        # Initialize with validated config
        config = InitializationConfig(**stack_config)

        # Validate provider configurations
        if config.k8s_provider:
            # Add provider-specific validation here
            pass

        return config

    except ValidationError as e:
        log.error(f"Invalid initialization configuration: {str(e)}")
        raise ValueError(f"Invalid initialization configuration: {str(e)}")
    except Exception as e:
        log.error(f"Configuration initialization failed: {str(e)}")
        raise


def get_enabled_modules(config: pulumi.Config) -> List[str]:
    """
    Returns a list of module names that are enabled in the configuration.

    Args:
        config: The Pulumi configuration object.

    Returns:
        A list of enabled module names.
    """

    # TODO: Implement dynamic module defaults loading via dynamic module discovery and loading.
    DEFAULT_MODULE_CONFIG = {}
    enabled_modules = []
    for module_name, module_defaults in DEFAULT_MODULE_CONFIG.items():
        # Get the configuration value with proper error handling
        config_key = f"konductor:{module_name}:enabled"
        is_enabled = config.get_bool(config_key)

        # Use default if no config value found
        if is_enabled is None:
            is_enabled = module_defaults["enabled"]

        log.info(f"Module {module_name} enabled status: {is_enabled}")
        if is_enabled:
            enabled_modules.append(module_name)

    return enabled_modules


def get_stack_outputs(init_config: InitializationConfig) -> StackOutputs:
    """
    Generate standardized stack outputs.

    Args:
        init_config: The initialization configuration object

    Returns:
        StackOutputs: Dictionary containing all stack outputs
    """
    try:
        # Get compliance data
        compliance_data = init_config.compliance_config or {}

        # Get configuration subset
        config_data = {
            "stack_name": init_config.stack_name,
            "project_name": init_config.project_name,
            "configurations": init_config.configurations,
        }

        # Construct the StackOutputs TypedDict
        stack_outputs: StackOutputs = {
            "compliance": compliance_data,
            "config": config_data,
        }

        return stack_outputs

    except Exception as e:
        log.error(f"Failed to generate stack outputs: {str(e)}")
        raise
