# src/core/interfaces/provider.py

"""
Provider interfaces.

Defines interfaces for providers and provider registry.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .resource import IResource


class IProvider(ABC):
    """Interface for infrastructure providers.

    This interface defines the contract for all providers in the framework,
    providing a consistent API for creating and managing resources.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the provider version.

        Returns:
            Provider version
        """
        pass

    @abstractmethod
    def create_resource(self, resource_type: str, name: str, **properties) -> 'IResource':
        """Create a new resource.

        Args:
            resource_type: Resource type
            name: Resource name
            properties: Resource properties

        Returns:
            Created resource
        """
        pass

    @abstractmethod
    def get_resource_types(self) -> Set[str]:
        """Get all supported resource types.

        Returns:
            Set of resource type identifiers
        """
        pass

    @abstractmethod
    def get_resource_schema(self, resource_type: str) -> Dict[str, Any]:
        """Get schema for a resource type.

        Args:
            resource_type: Resource type

        Returns:
            JSON schema
        """
        pass

    @abstractmethod
    def is_resource_type_supported(self, resource_type: str) -> bool:
        """Check if a resource type is supported.

        Args:
            resource_type: Resource type

        Returns:
            True if supported, otherwise False
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate provider credentials.

        Returns:
            True if valid, otherwise False
        """
        pass


class IProviderRegistry(ABC):
    """Interface for provider registry.

    This interface defines the contract for managing providers in the framework.
    """

    @abstractmethod
    def register_provider(self, provider: 'IProvider') -> None:
        """Register a provider.

        Args:
            provider: Provider to register
        """
        pass

    @abstractmethod
    def get_provider(self, provider_name: str) -> Optional['IProvider']:
        """Get a provider by name.

        Args:
            provider_name: Provider name

        Returns:
            Provider if registered, otherwise None
        """
        pass

    @abstractmethod
    def get_all_providers(self) -> Dict[str, 'IProvider']:
        """Get all registered providers.

        Returns:
            Dictionary of provider name to provider
        """
        pass

    @abstractmethod
    def is_provider_registered(self, provider_name: str) -> bool:
        """Check if a provider is registered.

        Args:
            provider_name: Provider name

        Returns:
            True if registered, otherwise False
        """
        pass

    @abstractmethod
    def get_provider_for_resource_type(self, resource_type: str) -> Optional['IProvider']:
        """Get the provider that supports a resource type.

        Args:
            resource_type: Resource type

        Returns:
            Provider if found, otherwise None
        """
        pass

    @abstractmethod
    def get_providers_supporting_resource_type(
        self, resource_type: str
    ) -> List['IProvider']:
        """Get all providers that support a resource type.

        Args:
            resource_type: Resource type

        Returns:
            List of providers
        """
        pass

    @abstractmethod
    def initialize_providers(self) -> None:
        """Initialize all registered providers."""
        pass
