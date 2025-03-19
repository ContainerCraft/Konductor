# src/core/config/defaults.py

"""Default configuration values for the IaC framework.

This module provides fallback default configurations when values are
not specified in the primary configuration source (Pulumi stack YAML).
These defaults ensure that the framework can operate with minimal
configuration while encouraging proper configuration through the stack.
"""

from typing import Dict, Any

# Core configuration defaults
DEFAULT_PROJECT_CONFIG: Dict[str, Any] = {
    "name": "default-project",
    "environment": "dev",
    "organization": "default-org"
}

# Default logging configuration
DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "level": "info",
    "format": "text",
    "console": False
}

# Provider defaults (disabled by default)
DEFAULT_AWS_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "region": "us-west-2"
}

DEFAULT_AZURE_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "location": "westus2"
}

DEFAULT_KUBERNETES_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "context": "default"
}

# Complete default configuration
DEFAULT_CONFIGURATION: Dict[str, Any] = {
    "project": DEFAULT_PROJECT_CONFIG,
    "logging": DEFAULT_LOGGING_CONFIG,
    "aws": DEFAULT_AWS_CONFIG,
    "azure": DEFAULT_AZURE_CONFIG,
    "kubernetes": DEFAULT_KUBERNETES_CONFIG,
    "providers": {
        "enabled": True  # Global provider enablement switch
    }
}


def get_default_config() -> Dict[str, Any]:
    """Get a copy of the default configuration.

    Returns:
        Dict containing default configuration values.
    """
    # Return a copy to ensure the defaults can't be modified
    return DEFAULT_CONFIGURATION.copy()
