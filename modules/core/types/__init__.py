# ./modules/core/types/__init__.py
"""
Core module types implementation.

This module defines all shared data classes and types used across all modules.
It provides type-safe configuration structures using Pydantic models and TypedDict.
"""

from .base import (
    ResourceBase,
    ConfigBase,
    GitInfo,
    InitializationConfig,
    ModuleRegistry,
    ModuleBase,
)
from .compliance import (
    FismaConfig,
    NistConfig,
    ScipConfig,
    ComplianceConfig,
)
from .config import (
    ModuleDefaults,
    ConfigurationValidator,
    StackOutputs,
)
from .metadata import (
    GlobalMetadata,
    ResourceMetadata,
    StackConfig,
)
from .interfaces import (
    ModuleDeploymentResult,
    DeploymentContext,
    ModuleInterface,
    ResourceManagerInterface,
)

__all__ = [
    # Base types
    "ResourceBase",
    "ConfigBase",
    "GitInfo",
    "InitializationConfig",
    "ModuleRegistry",
    "ModuleBase",
    # Compliance types
    "FismaConfig",
    "NistConfig",
    "ScipConfig",
    "ComplianceConfig",
    # Config types
    "ModuleDefaults",
    "ConfigurationValidator",
    "StackOutputs",
    # Metadata types
    "GlobalMetadata",
    "ResourceMetadata",
    "StackConfig",
    # Interfaces
    "ModuleDeploymentResult",
    "DeploymentContext",
    "ModuleInterface",
    "ResourceManagerInterface",
]
