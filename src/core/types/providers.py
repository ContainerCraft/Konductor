# src/core/types/providers.py

"""
Provider interface definitions for the Core Module.

This module provides the abstract interfaces for infrastructure providers,
which are responsible for creating, updating, and deleting resources
in specific cloud or on-premises environments.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, TypeVar, Any, Set, TYPE_CHECKING
import uuid
from dataclasses import dataclass

from .base import MetadataType

# To avoid circular imports
if TYPE_CHECKING:
    from .resources import Resource
    from ..interfaces.resource import IResource

from ..interfaces.provider import IProvider, IProviderRegistry


T = TypeVar('T', bound='Resource')


@dataclass
class ProviderOptions:
    """Common configuration options for providers."""
    region: str = ""
    zone: str = ""
    project: str = ""
    namespace: str = "default"
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


class Provider(ABC, IProvider):
    """Implementation of the IProvider interface.
    
    A Provider is responsible for translating infrastructure resource definitions 
    into actual cloud resources through the provider's API or SDK.
    """
    
    def __init__(self, name: str, version: str, options: Optional[ProviderOptions] = None):
        """Initialize a provider.
        
        Args:
            name: Provider name (e.g., 'aws', 'azure', 'gcp')
            version: Provider version
            options: Provider-specific options
        """
        self._name = name
        self._version = version
        self.options = options or ProviderOptions()
        self.id = str(uuid.uuid4())
        self.metadata = MetadataType(f"{name}-provider-metadata")
        self.supported_resource_types: Set[str] = set()
        
    @property
    def name(self) -> str:
        """Get the provider name.
        
        Returns:
            Provider name
        """
        return self._name
        
    @property
    def version(self) -> str:
        """Get the provider version.
        
        Returns:
            Provider version
        """
        return self._version
    
    @abstractmethod
    def create_resource(self, resource_type: str, name: str, **properties) -> IResource:
        """Create a new resource.
        
        Args:
            resource_type: Resource type
            name: Resource name
            properties: Resource properties
            
        Returns:
            New resource instance
        """
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate provider credentials.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        pass
    
    def supports_resource_type(self, resource_type: str) -> bool:
        """Check if this provider supports a resource type.
        
        Args:
            resource_type: Resource type to check
            
        Returns:
            True if supported, False otherwise
        """
        return resource_type in self.supported_resource_types
    
    def add_supported_resource_type(self, resource_type: str) -> None:
        """Add a supported resource type.
        
        Args:
            resource_type: Resource type to add
        """
        self.supported_resource_types.add(resource_type)
    
    def get_supported_resource_types(self) -> Set[str]:
        """Get all supported resource types.
        
        Returns:
            Set of supported resource types
        """
        return self.supported_resource_types


class ProviderFactory(ABC):
    """Factory for creating provider instances.
    
    This abstraction allows for creation of provider instances with
    specific configurations and credentials.
    """
    
    @abstractmethod
    def create_provider(self, options: Optional[ProviderOptions] = None) -> Provider:
        """Create a new provider instance.
        
        Args:
            options: Configuration options for the provider
            
        Returns:
            New provider instance
        """
        pass
    
    @staticmethod
    def get_factory(provider_type: str) -> Optional['ProviderFactory']:
        """Get a provider factory by provider type.
        
        This is a registry method that returns the appropriate factory
        for the specified provider type.
        
        Args:
            provider_type: Type of provider (e.g., 'aws', 'azure')
            
        Returns:
            Provider factory if available, None otherwise
        """
        registry = ProviderRegistry()
        return registry.get_factory(provider_type)


class ProviderRegistry(IProviderRegistry):
    """Implementation of the IProviderRegistry interface.
    
    This singleton class maintains a registry of provider factories that
    can be used to create provider instances for different cloud platforms.
    """
    
    _instance: Optional['ProviderRegistry'] = None
    _factories: Dict[str, Type[ProviderFactory]]
    _providers: Dict[str, IProvider]
    _resource_type_mapping: Dict[str, List[str]]
    
    def __new__(cls) -> 'ProviderRegistry':
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._factories = {}
            cls._instance._providers = {}
            cls._instance._resource_type_mapping = {}
        return cls._instance
    
    def register_provider(self, provider: IProvider) -> None:
        """Register a provider.
        
        Args:
            provider: Provider to register
        """
        if provider.name not in self._providers:
            self._providers[provider.name] = provider
            # Register supported resource types
            for resource_type in provider.get_supported_resource_types():
                if resource_type not in self._resource_type_mapping:
                    self._resource_type_mapping[resource_type] = []
                self._resource_type_mapping[resource_type].append(provider.name)
    
    def get_provider(self, provider_name: str) -> Optional[IProvider]:
        """Get a provider by name.
        
        Args:
            provider_name: Provider name
            
        Returns:
            Provider if registered, otherwise None
        """
        return self._providers.get(provider_name)
    
    def get_all_providers(self) -> Dict[str, IProvider]:
        """Get all registered providers.
        
        Returns:
            Dictionary of provider name to provider
        """
        return self._providers
    
    def is_provider_registered(self, provider_name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            provider_name: Provider name
            
        Returns:
            True if registered, otherwise False
        """
        return provider_name in self._providers
    
    def get_provider_for_resource_type(self, resource_type: str) -> Optional[IProvider]:
        """Get the provider that supports a resource type.
        
        Args:
            resource_type: Resource type
            
        Returns:
            Provider if found, otherwise None
        """
        if resource_type in self._resource_type_mapping and self._resource_type_mapping[resource_type]:
            provider_name = self._resource_type_mapping[resource_type][0]
            return self._providers.get(provider_name)
        return None
    
    def get_providers_supporting_resource_type(self, resource_type: str) -> List[IProvider]:
        """Get all providers that support a resource type.
        
        Args:
            resource_type: Resource type
            
        Returns:
            List of providers
        """
        if resource_type not in self._resource_type_mapping:
            return []
            
        return [self._providers[name] for name in self._resource_type_mapping[resource_type] 
                if name in self._providers]
    
    def initialize_providers(self) -> None:
        """Initialize all registered providers."""
        for provider in self._providers.values():
            provider.validate_credentials()
            
    # Additional methods to support ProviderFactory registration
    
    def register_factory(self, provider_type: str, factory_class: Type[ProviderFactory]) -> None:
        """Register a provider factory for a provider type.
        
        Args:
            provider_type: Type of provider (e.g., 'aws', 'azure')
            factory_class: Provider factory class to register
        """
        self._factories[provider_type] = factory_class
        
    def get_factory(self, provider_type: str) -> Optional[ProviderFactory]:
        """Get a provider factory instance by provider type.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            Provider factory instance if available, None otherwise
        """
        if factory_class := self._factories.get(provider_type):
            return factory_class()
        return None
    
    def list_providers(self) -> List[str]:
        """List all registered provider types.
        
        Returns:
            List of provider type names
        """
        return list(self._factories.keys())
