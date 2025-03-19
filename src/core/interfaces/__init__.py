# src/core/interfaces/__init__.py

"""
Core module interfaces.

This package provides high-level interfaces for the core module's functionality,
defining contracts between different subsystems and components.
"""

from .core_module import ICoreModule
from .logger import ILogger
from .config import IConfigManager
from .resource import IResource, IResourceManager
from .provider import IProvider, IProviderRegistry

__all__ = [
    'ICoreModule',
    'ILogger',
    'IConfigManager',
    'IResource',
    'IResourceManager',
    'IProvider',
    'IProviderRegistry',
]
