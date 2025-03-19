# src/core/types/exceptions.py

"""
Exceptions for the Core Module type system.

This module defines custom exceptions related to the type system and interfaces
to provide clear error messages and better error handling.
"""


class TypeError(Exception):
    """Base class for type-related exceptions."""
    pass


class PropertyTypeError(TypeError):
    """Raised when a property value doesn't match its expected type."""
    
    def __init__(self, property_name: str, expected_type: type, actual_type: type):
        self.property_name = property_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        message = f"Property '{property_name}' expected type {expected_type.__name__}, got {actual_type.__name__}"
        super().__init__(message)


class RequiredPropertyError(TypeError):
    """Raised when a required property is missing."""
    
    def __init__(self, property_name: str, resource_name: str):
        self.property_name = property_name
        self.resource_name = resource_name
        message = f"Required property '{property_name}' is missing for resource '{resource_name}'"
        super().__init__(message)


class ValidationError(Exception):
    """Base class for validation-related exceptions."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when validation against a schema fails."""
    
    def __init__(self, schema_name: str, error_details: str):
        self.schema_name = schema_name
        self.error_details = error_details
        message = f"Validation against schema '{schema_name}' failed: {error_details}"
        super().__init__(message)


class ResourceValidationError(ValidationError):
    """Raised when resource validation fails."""
    
    def __init__(self, resource_name: str, resource_type: str, error_details: str):
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.error_details = error_details
        message = f"Validation for resource '{resource_name}' of type '{resource_type}' failed: {error_details}"
        super().__init__(message)


class ProviderError(Exception):
    """Base class for provider-related exceptions."""
    pass


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not found."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        message = f"Provider '{provider_name}' not found"
        super().__init__(message)


class ResourceTypeNotSupportedError(ProviderError):
    """Raised when a provider doesn't support a requested resource type."""
    
    def __init__(self, provider_name: str, resource_type: str):
        self.provider_name = provider_name
        self.resource_type = resource_type
        message = f"Provider '{provider_name}' does not support resource type '{resource_type}'"
        super().__init__(message)


class ResourceOperationError(Exception):
    """Base class for resource operation exceptions."""
    pass


class ResourceCreationError(ResourceOperationError):
    """Raised when resource creation fails."""
    
    def __init__(self, resource_name: str, resource_type: str, error_details: str):
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.error_details = error_details
        message = f"Failed to create resource '{resource_name}' of type '{resource_type}': {error_details}"
        super().__init__(message)


class ResourceUpdateError(ResourceOperationError):
    """Raised when resource update fails."""
    
    def __init__(self, resource_name: str, resource_type: str, error_details: str):
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.error_details = error_details
        message = f"Failed to update resource '{resource_name}' of type '{resource_type}': {error_details}"
        super().__init__(message)


class ResourceDeletionError(ResourceOperationError):
    """Raised when resource deletion fails."""
    
    def __init__(self, resource_name: str, resource_type: str, error_details: str):
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.error_details = error_details
        message = f"Failed to delete resource '{resource_name}' of type '{resource_type}': {error_details}"
        super().__init__(message)


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected between resources."""
    
    def __init__(self, resources: list):
        self.resources = resources
        resource_names = [resource.name for resource in resources]
        message = f"Circular dependency detected between resources: {' -> '.join(resource_names)}"
        super().__init__(message)
