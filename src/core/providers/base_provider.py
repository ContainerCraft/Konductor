# src/core/providers/base_provider.py

"""Base provider implementation for the core module."""

import logging
from typing import Any, Dict, Optional, Set, List, TYPE_CHECKING

from ..interfaces.provider import IProvider
from ..types.validation import ResourceValidator, TypeValidator
from ..config import ConfigManager

if TYPE_CHECKING:
    from ..interfaces.resource import IResource
    from ..resources.base_resource import BaseResource


class BaseProvider(IProvider):
    """Base implementation of the provider interface.

    This class provides a concrete implementation of the IProvider interface
    that can be extended by specific provider implementations.
    """

    def __init__(self, name: str, version: str = "1.0.0", config_manager=None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the base provider.

        Args:
            name: The name of the provider.
            version: The version of the provider.
            config_manager: The configuration manager instance or None to create new one
            logger: Logger instance, or None to create a new one
        """
        self._name = name
        self._version = version
        self.config_manager = config_manager or ConfigManager()
        self.logger = logger or logging.getLogger(f"core.providers.{name}")
        self.supported_resource_types: Set[str] = set()
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.type_validator = TypeValidator()
        self.resource_validator = ResourceValidator()

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

    def initialize(self) -> bool:
        """Initialize the provider.

        Returns:
            True if initialization was successful, False otherwise.
        """
        self.logger.info(f"Initializing provider: {self.name}")
        return True

    def create_resource(
        self, resource_type: str, name: str, **properties
    ) -> 'IResource':
        """Create a new resource.

        Args:
            resource_type: Resource type
            name: Resource name
            properties: Resource properties

        Returns:
            Created resource
        """
        # This should be implemented by concrete provider classes
        raise NotImplementedError("create_resource must be implemented by subclasses")

    def get_resource_types(self) -> Set[str]:
        """Get all supported resource types.

        Returns:
            Set of resource type identifiers
        """
        return self.supported_resource_types.copy()

    def get_resource_schema(self, resource_type: str) -> Dict[str, Any]:
        """Get schema for a resource type.

        Args:
            resource_type: Resource type

        Returns:
            JSON schema
        """
        # This should be implemented by concrete provider classes
        raise NotImplementedError("get_resource_schema must be implemented by subclasses")

    def is_resource_type_supported(self, resource_type: str) -> bool:
        """Check if a resource type is supported.

        Args:
            resource_type: Resource type

        Returns:
            True if supported, otherwise False
        """
        return resource_type in self.supported_resource_types

    def validate_credentials(self) -> bool:
        """Validate provider credentials.

        Returns:
            True if valid, otherwise False
        """
        # This should be implemented by concrete provider classes
        return True
