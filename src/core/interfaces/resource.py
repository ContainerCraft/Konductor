# src/core/interfaces/resource.py

"""
Resource interfaces.

Defines interfaces for resources and resource management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from .provider import IProvider


class IResource(ABC):
    """Interface for infrastructure resources.

    This interface defines the contract for all resources in the framework,
    regardless of the underlying provider or resource type.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Get the resource ID.

        Returns:
            Unique identifier for this resource
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the resource name.

        Returns:
            Name of this resource
        """
        pass

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Get the resource type.

        Returns:
            Type identifier for this resource
        """
        pass

    @property
    @abstractmethod
    def provider(self) -> 'IProvider':
        """Get the provider that created this resource.

        Returns:
            Provider instance for this resource
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the resource configuration.

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def create(self) -> Dict[str, Any]:
        """Create the resource in the target infrastructure.

        Returns:
            Dictionary of outputs from the creation process
        """
        pass

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Read the current state of the resource from the infrastructure.

        Returns:
            Current state of the resource
        """
        pass

    @abstractmethod
    def update(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update the resource with new properties.

        Args:
            properties: New properties for the resource

        Returns:
            Updated state of the resource
        """
        pass

    @abstractmethod
    def delete(self) -> bool:
        """Delete the resource from the infrastructure.

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def add_dependency(self, resource: 'IResource') -> None:
        """Add a resource dependency.

        Args:
            resource: Resource dependency
        """
        pass

    @abstractmethod
    def get_dependencies(self) -> List['IResource']:
        """Get all dependencies for this resource.

        Returns:
            List of resource dependencies
        """
        pass


class IResourceManager(ABC):
    """Interface for resource management.

    This interface defines the contract for managing resources throughout
    their lifecycle, from creation to deletion.
    """

    @abstractmethod
    def register_resource(self, resource: 'IResource') -> None:
        """Register a resource with the manager.

        Args:
            resource: Resource to register
        """
        pass

    @abstractmethod
    def get_resource(self, resource_id: str) -> Optional['IResource']:
        """Get a resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Resource if found, otherwise None
        """
        pass

    @abstractmethod
    def get_resource_by_name(self, name: str) -> Optional['IResource']:
        """Get a resource by name.

        Args:
            name: Resource name

        Returns:
            Resource if found, otherwise None
        """
        pass

    @abstractmethod
    def get_resources_by_type(self, resource_type: str) -> List['IResource']:
        """Get all resources of a specific type.

        Args:
            resource_type: Resource type

        Returns:
            List of resources
        """
        pass

    @abstractmethod
    def get_resources_by_provider(self, provider_name: str) -> List['IResource']:
        """Get all resources for a specific provider.

        Args:
            provider_name: Provider name

        Returns:
            List of resources
        """
        pass

    @abstractmethod
    def get_all_resources(self) -> List['IResource']:
        """Get all registered resources.

        Returns:
            List of all resources
        """
        pass

    @abstractmethod
    def get_dependency_order(self) -> List['IResource']:
        """Get resources in dependency order.

        Returns:
            List of resources in dependency order
        """
        pass

    @abstractmethod
    def deploy_resources(self) -> Dict[str, Any]:
        """Deploy all registered resources.

        Returns:
            Dictionary of deployment outputs
        """
        pass

    @abstractmethod
    def destroy_resources(self) -> None:
        """Destroy all registered resources."""
        pass
