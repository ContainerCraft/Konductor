# src/core/interfaces/config.py

"""
Configuration manager interface.

Defines the interface for the configuration management subsystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class IConfigManager(ABC):
    """Interface for the configuration manager.

    This interface defines the contract for configuration management throughout
    the framework, providing access to configuration values and validation.
    """

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (dot-separated path)
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        pass

    @abstractmethod
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider.

        Args:
            provider: Provider name

        Returns:
            Provider configuration dictionary
        """
        pass

    @abstractmethod
    def get_credential(self, provider: str, credential_name: str) -> Optional[str]:
        """Get a credential for a provider.

        Args:
            provider: Provider name
            credential_name: Name of the credential

        Returns:
            Credential value or None if not found
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate the entire configuration against schemas.

        Returns:
            True if valid, otherwise False
        """
        pass

    @abstractmethod
    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a provider is enabled in the configuration.

        Args:
            provider: Provider name

        Returns:
            True if enabled, otherwise False
        """
        pass

    @abstractmethod
    def get_enabled_providers(self) -> List[str]:
        """Get a list of all enabled providers.

        Returns:
            List of enabled provider names
        """
        pass

    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        """Get the entire configuration.

        Returns:
            Configuration dictionary
        """
        pass
