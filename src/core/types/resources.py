# src/core/types/resources.py

"""
Resource interface definitions for the Core Module.

This module provides the abstract interfaces for resources, resource collections,
and stacks that form the foundation of the IaC model.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional, Iterator, Set, TypeVar, Generic
import uuid
from dataclasses import dataclass, field

from .base import ResourceType, MetadataType
from .providers import Provider
from ..interfaces.resource import IResource


class Resource(ResourceType, IResource):
    """Implementation of the IResource interface.

    A Resource represents a single infrastructure entity that can be created,
    updated, or deleted in a target provider environment.
    """

    def __init__(self, name: str, resource_type: str, provider: Provider):
        """Initialize a resource.

        Args:
            name: Unique name for this resource
            resource_type: Type identifier for this resource
            provider: Provider instance that will handle this resource
        """
        super().__init__(name, resource_type)
        self.provider = provider
        self.outputs: Dict[str, Any] = {}
        self.dependencies: List['IResource'] = []

        # Add provider-specific metadata
        self.metadata.set("provider", provider.name)
        self.metadata.set("provider_version", provider.version)
    
    @property
    def id(self) -> str:
        return super().id
    
    @property
    def name(self) -> str:
        return super().name
    
    @property
    def resource_type(self) -> str:
        return super().resource_type
    
    @property
    def provider_name(self) -> str:
        return self.provider.name
    
    def get_dependencies(self) -> List['IResource']:
        # Convert internal dependencies list to the interface type
        return self.dependencies
    
    def add_dependency(self, resource: 'IResource') -> None:
        if resource not in self.dependencies:
            self.dependencies.append(resource)

    @abstractmethod
    def create(self) -> Dict[str, Any]:
        """Create the resource in the target infrastructure.

        Returns:
            Dictionary of outputs from the creation
        """
        pass

    @abstractmethod
    def update(self) -> Dict[str, Any]:
        """Update the resource in the target infrastructure.

        Returns:
            Dictionary of outputs from the update
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """Delete the resource from the target infrastructure."""
        pass

    def get_outputs(self) -> Dict[str, Any]:
        """Get the current outputs of this resource.

        Returns:
            Dictionary of output values
        """
        return self.outputs

    def validate(self) -> bool:
        """Validate this resource's configuration.

        Returns:
            True if valid, otherwise False
        """
        # Check required properties
        for prop_name, prop in self.properties.items():
            if prop.required and prop.value is None:
                self.logger.error(
                    f"Required property '{prop_name}' is not set for "
                    f"resource '{self.name}'"
                )
                return False
        return True


T = TypeVar('T', bound=Resource)


class ResourceCollection(Generic[T]):
    """A collection of related resources.

    This serves as a container for managing multiple resources as a unit.
    """

    def __init__(self, name: str):
        """Initialize a resource collection.

        Args:
            name: Name of this collection
        """
        self.name = name
        self.id = str(uuid.uuid4())
        self.resources: Dict[str, T] = {}
        self.metadata = MetadataType(f"{name}-collection-metadata")

    def add(self, resource: T) -> None:
        """Add a resource to the collection.

        Args:
            resource: Resource to add
        """
        self.resources[resource.name] = resource

    def get(self, name: str) -> Optional[T]:
        """Get a resource by name.

        Args:
            name: Name of the resource

        Returns:
            Resource if found, otherwise None
        """
        return self.resources.get(name)

    def remove(self, name: str) -> None:
        """Remove a resource from the collection.

        Args:
            name: Name of the resource to remove
        """
        if name in self.resources:
            del self.resources[name]

    def __iter__(self) -> Iterator[T]:
        """Iterate over resources in the collection.

        Returns:
            Iterator of resources
        """
        return iter(self.resources.values())

    def __len__(self) -> int:
        """Get the number of resources in the collection.

        Returns:
            Number of resources
        """
        return len(self.resources)

    def __contains__(self, name: str) -> bool:
        """Check if a resource exists in the collection.

        Args:
            name: Name of the resource

        Returns:
            True if resource exists, otherwise False
        """
        return name in self.resources


@dataclass
class StackOptions:
    """Options for stack deployment."""

    parallel: bool = True
    max_concurrent: int = 10
    timeout_seconds: int = 600
    fail_fast: bool = True
    tags: Dict[str, str] = field(default_factory=dict)


class Stack(ResourceCollection[Resource]):
    """A deployable unit of resources.

    A Stack represents a collection of resources that are deployed together
    with a specific order based on dependencies.
    """

    def __init__(self, name: str, options: Optional[StackOptions] = None):
        """Initialize a stack.

        Args:
            name: Name of this stack
            options: Deployment options
        """
        super().__init__(name)
        self.options = options or StackOptions()
        self.dependencies: List['Stack'] = []
        self.outputs: Dict[str, Any] = {}

    def add_dependency(self, stack: 'Stack') -> None:
        """Add a stack dependency.

        Args:
            stack: Stack dependency
        """
        if stack not in self.dependencies:
            self.dependencies.append(stack)

    def deploy(self) -> Dict[str, Any]:
        """Deploy all resources in this stack.

        Returns:
            Dictionary of deployment outputs
        """
        # First deploy dependencies
        for dep in self.dependencies:
            dep.deploy()

        # Then deploy this stack's resources
        resources_by_dependency = self._sort_resources_by_dependencies()

        for resource_group in resources_by_dependency:
            # Deploy resources in this dependency level (can be parallelized)
            for resource in resource_group:
                try:
                    output = resource.create()
                    self.outputs[resource.name] = output
                except Exception as e:
                    if self.options.fail_fast:
                        raise e
                    # Otherwise, log error and continue
                    # This would be logged by resource.create()

        return self.outputs

    def destroy(self) -> None:
        """Destroy all resources in this stack."""
        # Sort resources in reverse dependency order
        resources_by_dependency = self._sort_resources_by_dependencies()
        resources_by_dependency.reverse()  # Reverse to destroy in opposite order

        for resource_group in resources_by_dependency:
            # Destroy resources in this dependency level (can be parallelized)
            for resource in resource_group:
                try:
                    resource.delete()
                except Exception as e:
                    if self.options.fail_fast:
                        raise e
                    # Otherwise, log error and continue

    def _sort_resources_by_dependencies(self) -> List[List[Resource]]:
        """Sort resources by dependencies for ordered deployment.

        Returns:
            List of resource groups, where each group can be deployed in parallel
        """
        # Simple topological sort implementation
        result: List[List[Resource]] = []
        visited: Set[str] = set()

        # Helper function to process a resource and its dependencies
        def process_resource(resource: Resource, current_path: Set[str] = None) -> None:
            if current_path is None:
                current_path = set()

            # Check for circular dependencies
            if resource.id in current_path:
                raise ValueError(
                    f"Circular dependency detected for resource '{resource.name}'"
                )

            # Skip if already visited
            if resource.id in visited:
                return

            # Process dependencies first
            current_path.add(resource.id)
            for dep in resource.dependencies:
                process_resource(dep, current_path)
            current_path.remove(resource.id)

            # Add resource to result at appropriate level
            if not resource.dependencies:
                # No dependencies, add to first level if it doesn't exist
                if not result:
                    result.append([])
                result[0].append(resource)
            else:
                # Find the max level of dependencies
                max_level = 0
                for dep in resource.dependencies:
                    for i, level in enumerate(result):
                        if dep in level:
                            max_level = max(max_level, i + 1)

                # Add resource at appropriate level
                while len(result) <= max_level:
                    result.append([])
                result[max_level].append(resource)

            visited.add(resource.id)

        # Process all resources
        for resource in self.resources.values():
            process_resource(resource)

        return result
