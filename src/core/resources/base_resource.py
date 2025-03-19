# src/core/resources/base_resource.py

"""Base resource implementation for the core module."""

import uuid
from typing import Dict, List, Any, TYPE_CHECKING

from ..interfaces.resource import IResource

if TYPE_CHECKING:
    from ..interfaces.provider import IProvider


class BaseResource(IResource):
    """Base implementation of the resource interface.

    This class provides a concrete implementation of the IResource interface
    that can be extended by specific resource implementations.
    """

    def __init__(self, name: str, resource_type: str, provider: 'IProvider'):
        """Initialize the base resource.

        Args:
            name: The name of the resource
            resource_type: The type of the resource
            provider: Provider instance that will handle this resource
        """
        self._name = name
        self._resource_type = resource_type
        self._provider = provider
        self._id = str(uuid.uuid4())
        self._properties: Dict[str, Any] = {}
        self._dependencies: List['IResource'] = []
        self._outputs: Dict[str, Any] = {}

    @property
    def id(self) -> str:
        """Get the resource ID.

        Returns:
            Unique identifier for this resource
        """
        return self._id

    @property
    def name(self) -> str:
        """Get the resource name.

        Returns:
            Name of this resource
        """
        return self._name

    @property
    def resource_type(self) -> str:
        """Get the resource type.

        Returns:
            Type identifier for this resource
        """
        return self._resource_type

    @property
    def provider(self) -> 'IProvider':
        """Get the provider that created this resource.

        Returns:
            Provider instance for this resource
        """
        return self._provider

    def validate(self) -> bool:
        """Validate the resource configuration.

        Returns:
            True if valid, False otherwise
        """
        # Basic implementation - should be overridden by specific resources
        return True

    def create(self) -> Dict[str, Any]:
        """Create the resource in the target infrastructure.

        Returns:
            Dictionary of outputs from the creation process
        """
        # This should be implemented by the specific resource classes
        raise NotImplementedError("Create method must be implemented by subclasses")

    def read(self) -> Dict[str, Any]:
        """Read the current state of the resource from the infrastructure.

        Returns:
            Current state of the resource
        """
        # This should be implemented by the specific resource classes
        raise NotImplementedError("Read method must be implemented by subclasses")

    def update(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update the resource with new properties.

        Args:
            properties: New properties for the resource

        Returns:
            Updated state of the resource
        """
        # This should be implemented by the specific resource classes
        raise NotImplementedError("Update method must be implemented by subclasses")

    def delete(self) -> bool:
        """Delete the resource from the infrastructure.

        Returns:
            True if deletion was successful, False otherwise
        """
        # This should be implemented by the specific resource classes
        raise NotImplementedError("Delete method must be implemented by subclasses")

    def add_dependency(self, resource: 'IResource') -> None:
        """Add a resource dependency.

        Args:
            resource: Resource dependency
        """
        if resource not in self._dependencies:
            self._dependencies.append(resource)

    def get_dependencies(self) -> List['IResource']:
        """Get all dependencies for this resource.

        Returns:
            List of resource dependencies
        """
        return self._dependencies.copy()
