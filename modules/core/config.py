# ./modules/core/config.py

"""
Configuration Management Module

This module handles retrieval and preparation of configurations for different modules
within the Pulumi IaC program. It centralizes configuration logic to promote reuse
and maintainability.
"""

import pulumi
from pulumi import log
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, List, cast

from .types import (
    InitializationConfig,
    ModuleBase,
    StackOutputs,
    ComplianceConfig,
    StackConfig,
)

# Default Cache Directory Path
CACHE_DIR = Path("/tmp/konductor")


class ConfigManager:
    """Manages configuration retrieval and caching for modules."""

    def __init__(self, pulumi_config: pulumi.Config) -> None:
        """Initialize the ConfigManager with a Pulumi config object."""
        self.pulumi_config = pulumi_config
        self._module_configs: Dict[str, Dict[str, Any]] = {}
        log.debug("Initialized ConfigManager with full config")

    def get_enabled_modules(self) -> List[str]:
        """Returns list of enabled module names from modules/ directory."""
        enabled_modules: List[str] = []

        # Get all module directories (excluding core, __pycache__, etc)
        modules_dir = Path(__file__).parent.parent
        available_modules = [
            item.name for item in modules_dir.iterdir()
            if item.is_dir() and
            item.name not in ['core', '__pycache__'] and
            not item.name.startswith('_')
        ]

        # Check each module's config for enabled=true
        for module_name in available_modules:
            config = self.pulumi_config.get_object(module_name) or {}
            if config.get("enabled", False):
                enabled_modules.append(module_name)
                log.info(f"Module {module_name} is enabled")
            else:
                log.debug(f"Module {module_name} is disabled")

        return enabled_modules

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get module's config from Pulumi config."""
        if module_name not in self._module_configs:
            config = self.pulumi_config.get_object(module_name) or {}
            self._module_configs[module_name] = config
        return self._module_configs[module_name]


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
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        required_fields = {"enabled"}
        if missing := required_fields - set(config.keys()):
            raise ValueError(f"Missing required fields: {missing}")

        if module_class:
            module_class(**config)

    except Exception as e:
        msg = f"Configuration validation failed for {module_name}: {str(e)}"
        log.error(msg)
        raise ValueError(msg) from e


def merge_configurations(
    base_config: Dict[str, Any],
    override_config: Dict[str, Any]
) -> Dict[str, Any]:
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
        if (
            key in result and
            isinstance(result[key], dict) and
            isinstance(value, dict)
        ):
            result[key] = merge_configurations(result[key], value)
        else:
            result[key] = value
    return result


def export_results(
    configurations: Dict[str, Dict[str, Any]],
    compliance: ComplianceConfig,
) -> None:
    """
    Exports deployment results including configurations and compliance information.

    Args:
        configurations: Configurations of deployed modules.
        compliance: Compliance configuration.

    Raises:
        RuntimeError: If export fails
    """
    try:
        compliance_dict = (
            compliance.dict() if hasattr(compliance, "dict")
            else compliance
        )
        pulumi.export("configuration", configurations)
        pulumi.export("compliance", compliance_dict)

    except Exception as e:
        log.error(f"Failed to export results: {str(e)}")
        raise RuntimeError(f"Failed to export results: {str(e)}") from e


def get_stack_outputs(init_config: InitializationConfig) -> StackOutputs:
    """
    Generate standardized stack outputs.

    Args:
        init_config: The initialization configuration object

    Returns:
        StackOutputs: Dictionary containing all stack outputs

    Raises:
        RuntimeError: If stack outputs generation fails
    """
    try:
        compliance_data = (
            init_config.compliance_config.dict()
            if hasattr(init_config.compliance_config, "dict")
            else init_config.compliance_config
        )

        return StackOutputs(
            stack=StackConfig(
                compliance=compliance_data,
                metadata=init_config.metadata.dict(),
                source_repository=init_config.git_info.dict(),
            ),
            secrets=None,
        )

    except Exception as e:
        log.error(f"Failed to generate stack outputs: {str(e)}")
        raise RuntimeError(f"Failed to generate stack outputs: {str(e)}") from e


__all__ = [
    "ConfigManager",
    "validate_module_config",
    "merge_configurations",
    "export_results",
    "get_stack_outputs",
]
