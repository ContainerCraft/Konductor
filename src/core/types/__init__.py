# src/core/types/__init__.py

"""
Core Type System and Interfaces for the IaC framework.

This module provides the foundation for type definitions, resource interfaces,
and provider abstractions used throughout the framework. It establishes a consistent
type hierarchy and enforces structural patterns through abstract base classes.
"""

# Base type definitions
from .base import ResourceType, PropertyType, MetadataType, ComponentType

# Resource interfaces
from .resources import Resource, ResourceCollection, Stack

# Provider interfaces
from .providers import Provider, ProviderFactory

# All public exports
__all__ = [
    # Base types
    'ResourceType',
    'PropertyType',
    'MetadataType',
    'ComponentType',

    # Resource interfaces
    'Resource',
    'ResourceCollection',
    'Stack',

    # Provider interfaces
    'Provider',
    'ProviderFactory',
]
