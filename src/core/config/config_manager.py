# src/core/config/config_manager.py

"""Configuration management for the core module."""

import pulumi
from typing import Dict, Any


class ConfigManager:
    """Manages configuration loading, validation, and propagation."""

    def __init__(self):
        """Initialize the configuration manager."""
        self.config = pulumi.Config()

    def _get_project_config(self) -> Dict[str, Any]:
        """Get the project configuration.

        Returns:
            Dict containing project configuration.
        """
        try:
            return self.config.get_object("project")
        except Exception:
            # Fallback to default configuration if none provided
            return {
                "name": "default-project",
                "environment": "dev"
            }

    def get_provider_config(self, provider_type: str) -> Dict[str, Any]:
        """Get the configuration for a specific provider.

        Args:
            provider_type: The type of provider (e.g., 'aws', 'azure', 'kubernetes').

        Returns:
            Dict containing provider configuration.
        """
        # In MVP, just return an empty dict
        return {}

    def is_provider_enabled(self, provider_type: str) -> bool:
        """Check if a provider is enabled in the configuration.

        Args:
            provider_type: The type of provider (e.g., 'aws', 'azure', 'kubernetes').

        Returns:
            True if the provider is enabled, False otherwise.
        """
        # In MVP, all providers are disabled by default
        return False
