# src/core/interfaces/core_module.py

"""
Core Module interface.

Defines the contract for the main Core Module service.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

# Import interfaces to resolve undefined name errors
from .logger import ILogger
from .config import IConfigManager
from .provider import IProvider, IProviderRegistry
from .resource import IResource, IResourceManager


class ICoreModule(ABC):
    """Interface for the Core Module.

    The core module is the main entry point for the IaC framework, providing
    access to all subsystems and components.
    """

    @property
    @abstractmethod
    def logger(self) -> ILogger:
        """Get the logger.

        Returns:
            Logger instance
        """
        pass

    @property
    @abstractmethod
    def config(self) -> IConfigManager:
        """Get the configuration manager.

        Returns:
            Configuration manager instance
        """
        pass

    @property
    @abstractmethod
    def provider_registry(self) -> IProviderRegistry:
        """Get the provider registry.

        Returns:
            Provider registry instance
        """
        pass

    @property
    @abstractmethod
    def resource_manager(self) -> IResourceManager:
        """Get the resource manager.

        Returns:
            Resource manager instance
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the core module and all subsystems."""
        pass

    @abstractmethod
    def get_provider(self, provider_type: str) -> IProvider:
        """Get a provider by type.

        Args:
            provider_type: Provider type identifier

        Returns:
            Provider instance
        """
        pass

    @abstractmethod
    def create_resource(
        self, provider_type: str, resource_type: str, name: str, **properties
    ) -> IResource:
        """Create a new resource.

        Args:
            provider_type: Provider type identifier
            resource_type: Resource type identifier
            name: Name for the new resource
            properties: Resource properties

        Returns:
            Created resource
        """
        pass

    @abstractmethod
    def deploy(self) -> Dict[str, Any]:
        """Deploy all resources.

        Returns:
            Dictionary of deployment outputs
        """
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Destroy all resources."""
        pass
