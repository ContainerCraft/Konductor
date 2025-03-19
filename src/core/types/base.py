# src/core/types/base.py

"""
Base type definitions for the Core Module type system.

This module provides the fundamental type definitions that serve as building blocks
for the entire IaC framework. It defines abstract base classes for resources,
properties, components, and metadata.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Set, Type
import uuid
import logging
from ..config import ConfigManager


class BaseType(ABC):
    """Base class for all type definitions in the framework."""
    
    def __init__(self, name: str):
        """Initialize a base type with a name.
        
        Args:
            name: Unique name for this type instance
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.logger = logging.getLogger(f"core.types.{self.__class__.__name__.lower()}")


class PropertyType(BaseType):
    """Represents a typed property with validation."""
    
    def __init__(self, name: str, value_type: Type, required: bool = False, 
                 default: Any = None, description: str = ""):
        """Initialize a property type.
        
        Args:
            name: Name of the property
            value_type: Expected type for the property value
            required: Whether this property is required
            default: Default value if none is provided
            description: Description of the property
        """
        super().__init__(name)
        self.value_type = value_type
        self.required = required
        self.default = default
        self.description = description
        self._value = default
    
    @property
    def value(self) -> Any:
        """Get the property value."""
        return self._value
    
    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the property value with type validation.
        
        Args:
            new_value: New value to set
            
        Raises:
            TypeError: If value type doesn't match expected type
        """
        if new_value is not None and not isinstance(new_value, self.value_type):
            raise TypeError(
                f"Property '{self.name}' expected type {self.value_type.__name__}, "
                f"got {type(new_value).__name__}"
            )
        self._value = new_value


class MetadataType(BaseType):
    """Container for resource metadata."""
    
    def __init__(self, name: str):
        """Initialize metadata container.
        
        Args:
            name: Name for this metadata container
        """
        super().__init__(name)
        self._metadata: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.
        
        Args:
            key: Metadata key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a metadata value.
        
        Args:
            key: Metadata key
            value: Value to store
        """
        self._metadata[key] = value
    
    def update(self, values: Dict[str, Any]) -> None:
        """Update multiple metadata values.
        
        Args:
            values: Dictionary of values to update
        """
        self._metadata.update(values)
    
    def keys(self) -> Set[str]:
        """Get all metadata keys.
        
        Returns:
            Set of all metadata keys
        """
        return set(self._metadata.keys())
    
    def __contains__(self, key: str) -> bool:
        """Check if metadata contains a key.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, otherwise False
        """
        return key in self._metadata


T = TypeVar('T', bound='ResourceType')


class ResourceType(BaseType):
    """Base type for all infrastructure resources."""
    
    def __init__(self, name: str, resource_type: str):
        """Initialize a resource type.
        
        Args:
            name: Unique name for this resource
            resource_type: Type identifier for this resource (e.g., 'aws:s3:bucket')
        """
        super().__init__(name)
        self.resource_type = resource_type
        self.properties: Dict[str, PropertyType] = {}
        self.metadata = MetadataType(f"{name}-metadata")
        self.dependencies: List['ResourceType'] = []
    
    def add_property(self, prop: PropertyType) -> None:
        """Add a property to this resource.
        
        Args:
            prop: Property to add
        """
        self.properties[prop.name] = prop
    
    def get_property(self, name: str) -> Any:
        """Get a property value.
        
        Args:
            name: Name of the property
            
        Returns:
            Property value
            
        Raises:
            KeyError: If property doesn't exist
        """
        if name not in self.properties:
            raise KeyError(f"Property '{name}' not found in resource '{self.name}'")
        return self.properties[name].value
    
    def set_property(self, name: str, value: Any) -> None:
        """Set a property value.
        
        Args:
            name: Name of the property
            value: Value to set
            
        Raises:
            KeyError: If property doesn't exist
        """
        if name not in self.properties:
            raise KeyError(f"Property '{name}' not found in resource '{self.name}'")
        self.properties[name].value = value
    
    def add_dependency(self, resource: 'ResourceType') -> None:
        """Add a dependency to this resource.
        
        Args:
            resource: Resource dependency
        """
        if resource not in self.dependencies:
            self.dependencies.append(resource)
    
    def validate(self) -> bool:
        """Validate this resource's properties.
        
        Returns:
            True if valid, otherwise False
        """
        # Check required properties
        for prop_name, prop in self.properties.items():
            if prop.required and prop.value is None:
                self.logger.error(f"Required property '{prop_name}' not set in resource '{self.name}'")
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary.
        
        Returns:
            Dictionary representation of the resource
        """
        return {
            'id': self.id,
            'name': self.name,
            'resource_type': self.resource_type,
            'properties': {name: prop.value for name, prop in self.properties.items()},
            'metadata': self.metadata._metadata,
            'dependencies': [dep.id for dep in self.dependencies]
        }


class ComponentType(ResourceType):
    """A logical grouping of related resources."""
    
    def __init__(self, name: str, description: str = ""):
        """Initialize a component.
        
        Args:
            name: Unique name for this component
            description: Description of what this component represents
        """
        super().__init__(name, "component")
        self.description = description
        self.resources: List[ResourceType] = []
        
    def add_resource(self, resource: ResourceType) -> None:
        """Add a resource to this component.
        
        Args:
            resource: Resource to add
        """
        if resource not in self.resources:
            self.resources.append(resource)
            # Component implicitly depends on all its resources
            self.add_dependency(resource)
    
    def get_resources(self) -> List[ResourceType]:
        """Get all resources in this component.
        
        Returns:
            List of resources
        """
        return self.resources
    
    def get_resource_by_name(self, name: str) -> Optional[ResourceType]:
        """Get a resource by name.
        
        Args:
            name: Name of the resource
            
        Returns:
            Resource if found, otherwise None
        """
        for resource in self.resources:
            if resource.name == name:
                return resource
        return None
    
    def validate(self) -> bool:
        """Validate this component and all its resources.
        
        Returns:
            True if all valid, otherwise False
        """
        # First validate component itself
        if not super().validate():
            return False
        
        # Then validate all contained resources
        for resource in self.resources:
            if not resource.validate():
                self.logger.error(f"Resource '{resource.name}' in component '{self.name}' is not valid")
                return False
        
        return True
