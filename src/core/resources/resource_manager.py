# src/core/resources/resource_manager.py

"""Resource manager implementation.

Provides functionality for managing resources throughout their lifecycle.
"""

import logging
from typing import Dict, List, Optional, Set, Any

from ..interfaces.resource import IResource, IResourceManager
from ..types.exceptions import ResourceError, DependencyError


class ResourceManager(IResourceManager):
    """Resource manager implementation.
    
    This class provides functionality for managing resources throughout their
    lifecycle, including creation, registration, dependency tracking,
    validation, and deployment.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the resource manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("core.resources")
        self._resources: Dict[str, IResource] = {}
        self._resources_by_name: Dict[str, IResource] = {}
        self._resources_by_type: Dict[str, List[IResource]] = {}
        self._resources_by_provider: Dict[str, List[IResource]] = {}
        self.logger.info("Resource manager initialized")
    
    def register_resource(self, resource: IResource) -> None:
        """Register a resource with the manager.
        
        Args:
            resource: Resource to register
        """
        if resource.id in self._resources:
            self.logger.warning(
                f"Resource with ID {resource.id} already registered"
            )
            return
        
        self._resources[resource.id] = resource
        self._resources_by_name[resource.name] = resource
        
        # Add to type index
        if resource.resource_type not in self._resources_by_type:
            self._resources_by_type[resource.resource_type] = []
        self._resources_by_type[resource.resource_type].append(resource)
        
        # Add to provider index
        provider_name = resource.provider.name
        if provider_name not in self._resources_by_provider:
            self._resources_by_provider[provider_name] = []
        self._resources_by_provider[provider_name].append(resource)
        
        self.logger.info(
            f"Registered resource: {resource.name} ({resource.id})"
        )
    
    def get_resource(self, resource_id: str) -> Optional[IResource]:
        """Get a resource by ID.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            Resource if found, otherwise None
        """
        return self._resources.get(resource_id)
    
    def get_resource_by_name(self, name: str) -> Optional[IResource]:
        """Get a resource by name.
        
        Args:
            name: Resource name
            
        Returns:
            Resource if found, otherwise None
        """
        return self._resources_by_name.get(name)
    
    def get_resources_by_type(self, resource_type: str) -> List[IResource]:
        """Get all resources of a specific type.
        
        Args:
            resource_type: Resource type
            
        Returns:
            List of resources
        """
        return self._resources_by_type.get(resource_type, [])
    
    def get_resources_by_provider(self, provider_name: str) -> List[IResource]:
        """Get all resources for a specific provider.
        
        Args:
            provider_name: Provider name
            
        Returns:
            List of resources
        """
        return self._resources_by_provider.get(provider_name, [])
    
    def get_all_resources(self) -> List[IResource]:
        """Get all registered resources.
        
        Returns:
            List of all resources
        """
        return list(self._resources.values())
    
    def get_dependency_order(self) -> List[IResource]:
        """Get resources in dependency order.
        
        This performs a topological sort of the resource dependency graph
        to ensure resources are deployed in the correct order.
        
        Returns:
            List of resources in dependency order
        """
        # Track visited and added resources
        visited: Set[str] = set()
        added: Set[str] = set()
        ordered: List[IResource] = []
        
        def visit(resource_id: str) -> None:
            """Visit a resource and its dependencies recursively.
            
            Args:
                resource_id: Resource ID to visit
            """
            # Skip if already processed
            if resource_id in added:
                return
            
            # Detect cycles
            if resource_id in visited:
                msg = (
                    f"Circular dependency detected for resource {resource_id}"
                )
                raise DependencyError(msg)
            
            # Mark as visited
            visited.add(resource_id)
            
            # Get the resource
            resource = self._resources.get(resource_id)
            if not resource:
                raise ResourceError(
                    f"Resource {resource_id} not found"
                )
            
            # Visit dependencies first
            for dep in resource.get_dependencies():
                visit(dep.id)
            
            # Add to ordered list
            ordered.append(resource)
            added.add(resource_id)
        
        # Process all resources
        for resource_id in self._resources:
            if resource_id not in added:
                visit(resource_id)
        
        return ordered
    
    def deploy_resources(self) -> Dict[str, Any]:
        """Deploy all registered resources.
        
        Returns:
            Dictionary of deployment outputs
        """
        self.logger.info("Deploying resources")
        outputs = {}
        
        # Get resources in dependency order
        try:
            ordered_resources = self.get_dependency_order()
        except DependencyError as e:
            self.logger.error(
                f"Failed to determine deployment order: {e}"
            )
            raise
        
        # Deploy each resource in order
        for resource in ordered_resources:
            self.logger.info(
                f"Deploying resource: {resource.name} ({resource.id})"
            )
            try:
                resource_outputs = resource.create()
                outputs[resource.id] = resource_outputs
            except Exception as e:
                self.logger.error(
                    f"Failed to deploy resource {resource.name}: {e}"
                )
                raise
        
        return outputs
    
    def destroy_resources(self) -> None:
        """Destroy all registered resources."""
        self.logger.info("Destroying resources")
        
        # Get resources in reverse dependency order
        try:
            ordered_resources = list(reversed(self.get_dependency_order()))
        except DependencyError as e:
            self.logger.error(
                f"Failed to determine destruction order: {e}"
            )
            raise
        
        # Destroy each resource in reverse order
        for resource in ordered_resources:
            self.logger.info(
                f"Destroying resource: {resource.name} ({resource.id})"
            )
            try:
                resource.delete()
            except Exception as e:
                self.logger.error(
                    f"Failed to destroy resource {resource.name}: {e}"
                )
                # Continue with other resources even if one fails
