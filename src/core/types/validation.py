# src/core/types/validation.py

"""
Type validation utilities for the Core Module.

This module provides validators for runtime type checking and property validation
to ensure type safety throughout the system.
"""

import logging
from typing import Any, Dict, Type, Optional, Callable, TypeVar

from ..config import SchemaValidator
from .base import ResourceType


T = TypeVar('T')


class TypeValidator:
    """Validator for runtime type checking."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize a type validator.
        
        Args:
            logger: Logger instance, or None to create a new one
        """
        self.logger = logger or logging.getLogger("core.types.validator")
        self.schema_validator = SchemaValidator(self.logger)
    
    def validate_type(self, value: Any, expected_type: Type[T]) -> Optional[T]:
        """Validate that a value matches an expected type.
        
        Args:
            value: Value to validate
            expected_type: Expected type
            
        Returns:
            Value cast to expected type if valid, otherwise None
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, expected_type):
                return value
            
            # Handle some common type conversions
            if expected_type == int and isinstance(value, (str, float)):
                return int(value)
            
            if expected_type == float and isinstance(value, (str, int)):
                return float(value)
            
            if expected_type == bool and isinstance(value, str):
                if value.lower() in ('true', 'yes', '1'):
                    return True
                if value.lower() in ('false', 'no', '0'):
                    return False
            
            if expected_type == str:
                return str(value)
            
            self.logger.error(
                f"Type validation failed: expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
            return None
        
        except (ValueError, TypeError) as e:
            self.logger.error(f"Type conversion error: {str(e)}")
            return None
    
    def validate_dict_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate a dictionary against a schema.
        
        Args:
            data: Dictionary to validate
            schema: JSON schema
            
        Returns:
            True if valid, otherwise False
        """
        try:
            self.schema_validator.validate(data, schema)
            return True
        except Exception as e:
            self.logger.error(f"Schema validation error: {str(e)}")
            return False


class PropertyValidator:
    """Validator for resource properties."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize a property validator.
        
        Args:
            logger: Logger instance, or None to create a new one
        """
        self.logger = logger or logging.getLogger("core.types.property_validator")
        self.type_validator = TypeValidator(self.logger)
    
    def validate_property(
        self,
        name: str,
        value: Any,
        expected_type: Type,
        required: bool = False,
        custom_validator: Optional[Callable[[Any], bool]] = None
    ) -> bool:
        """Validate a property value.
        
        Args:
            name: Property name
            value: Property value
            expected_type: Expected type
            required: Whether the property is required
            custom_validator: Optional custom validation function
            
        Returns:
            True if valid, otherwise False
        """
        # Check if required
        if required and value is None:
            self.logger.error(f"Required property '{name}' is missing")
            return False
        
        # Skip validation for None values that aren't required
        if value is None and not required:
            return True
        
        # Validate type
        typed_value = self.type_validator.validate_type(value, expected_type)
        if typed_value is None:
            return False
        
        # Apply custom validator if provided
        if custom_validator is not None:
            try:
                if not custom_validator(typed_value):
                    self.logger.error(f"Custom validation failed for property '{name}'")
                    return False
            except Exception as e:
                self.logger.error(f"Error in custom validator for property '{name}': {str(e)}")
                return False
        
        return True


class ResourceValidator:
    """Validator for resources."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize a resource validator.
        
        Args:
            logger: Logger instance, or None to create a new one
        """
        self.logger = logger or logging.getLogger("core.types.resource_validator")
        self.property_validator = PropertyValidator(self.logger)
        self.schema_validator = SchemaValidator(self.logger)
    
    def validate_resource_properties(self, resource: ResourceType) -> bool:
        """Validate all properties of a resource.
        
        Args:
            resource: Resource to validate
            
        Returns:
            True if all properties are valid, otherwise False
        """
        for prop_name, prop in resource.properties.items():
            if not self.property_validator.validate_property(
                prop_name, prop.value, prop.value_type, prop.required
            ):
                return False
        return True
    
    def validate_resource_against_schema(self, resource: ResourceType, schema: Dict[str, Any]) -> bool:
        """Validate a resource against its JSON schema.
        
        Args:
            resource: Resource to validate
            schema: JSON schema for the resource type
            
        Returns:
            True if valid, otherwise False
        """
        # Convert resource properties to a dictionary
        props_dict = {name: prop.value for name, prop in resource.properties.items()}
        
        try:
            self.schema_validator.validate(props_dict, schema)
            return True
        except Exception as e:
            msg = (
                f"Schema validation failed for resource '{resource.name}' "
                f"of type '{resource.resource_type}': {str(e)}"
            )
            self.logger.error(msg)
            return False
