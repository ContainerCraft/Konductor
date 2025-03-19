# src/core/resources/stack.py

"""Stack implementation for resource collections."""

from typing import Dict, List, Any, Optional
from ..interfaces.resource import IResource


class Stack:
    """Stack implementation for managing resource collections.

    A Stack represents a collection of resources that are provisioned together.
    It provides functionality for managing the lifecycle of these resources.
    """

    def __init__(self, name: str):
        """Initialize a new stack.

        Args:
            name: Stack name
        """
        self.name = name
        self.resources: Dict[str, IResource] = {}
        self.outputs: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def add_resource(self, resource: IResource) -> None:
        """Add a resource to the stack.

        Args:
            resource: Resource to add
        """
        self.resources[resource.id] = resource

    def get_resource(self, resource_id: str) -> Optional[IResource]:
        """Get a resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Resource if found, otherwise None
        """
        return self.resources.get(resource_id)

    def get_resources(self) -> Dict[str, IResource]:
        """Get all resources in the stack.

        Returns:
            Dictionary of resources keyed by ID
        """
        return self.resources

    def set_output(self, key: str, value: Any) -> None:
        """Set a stack output.

        Args:
            key: Output key
            value: Output value
        """
        self.outputs[key] = value

    def get_outputs(self) -> Dict[str, Any]:
        """Get all stack outputs.

        Returns:
            Dictionary of outputs
        """
        return self.outputs

    def set_metadata(self, key: str, value: Any) -> None:
        """Set stack metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self) -> Dict[str, Any]:
        """Get stack metadata.

        Returns:
            Dictionary of metadata
        """
        return self.metadata

    def __str__(self) -> str:
        return f"Stack(name='{self.name}', resources={len(self.resources)})"
