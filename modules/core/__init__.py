# ../konductor/modules/core/__init__.py
"""
Konductor Core Module

This module provides the core functionality for the Konductor Infrastructure as Code platform.
It handles configuration management, deployment orchestration, resource management,
and compliance controls.

Key Components:
- Configuration Management: Handles configuration loading, validation, and merging
- Deployment Orchestration: Manages module deployment and dependencies
- Resource Management: Provides resource creation and transformation utilities
- Metadata Management: Handles global metadata and tagging
- Type Definitions: Defines core data structures and types

Usage:
    from pulumi.core import (
        initialize_pulumi,
        deploy_modules,
        ComplianceConfig,
        InitializationConfig
    )
"""

from typing import Dict, Any

# Version information
__version__ = "0.0.1"
__author__ = "ContainerCraft Konductor Maintainers"

# Type exports
from .types import (
    ComplianceConfig,
    InitializationConfig,
    ModuleBase,
    ModuleDefaults,
    FismaConfig,
    NistConfig,
    ScipConfig,
    StackOutputs,
)

# Interfaces
from .interfaces import (
    DeploymentContext,
    ModuleInterface,
    ModuleDeploymentResult,
    ResourceMetadata,
)

# Configuration management
from .config import (
    get_module_config,
    load_default_versions,
    export_results,
    validate_module_config,
    initialize_config,
    merge_configurations,
    DEFAULT_MODULE_CONFIG,
    get_stack_outputs,
)

# Metadata management
from .metadata import (
    setup_global_metadata,
    set_global_labels,
    set_global_annotations,
)

# Git utilities
from .git import (
    collect_git_info,
    get_latest_semver_tag,
    get_remote_url,
    sanitize_git_info,
    extract_repo_name,
)

# Utility functions
from .utils import (
    set_resource_metadata,
    generate_global_transformations,
)

# Initialization
from .initialization import initialize_pulumi

# Deployment
from .deployment import DeploymentManager

# Public API
__all__ = [
    # Types
    "ComplianceConfig",
    "InitializationConfig",
    "ModuleBase",
    "ModuleDefaults",
    "FismaConfig",
    "NistConfig",
    "ScipConfig",
    "StackOutputs",

    # Interfaces
    "DeploymentContext",
    "ModuleInterface",
    "ModuleDeploymentResult",
    "ResourceMetadata",

    # Configuration
    "get_module_config",
    "load_default_versions",
    "export_results",
    "validate_module_config",
    "initialize_config",
    "merge_configurations",
    "DEFAULT_MODULE_CONFIG",
    "get_stack_outputs",

    # Deployment
    "initialize_pulumi",

    # Metadata
    "setup_global_metadata",
    "set_global_labels",
    "set_global_annotations",

    # Git Utilities
    "collect_git_info",
    "get_latest_semver_tag",
    "get_remote_url",
    "sanitize_git_info",
    "extract_repo_name",

    # Utilities
    "set_resource_metadata",
    "generate_global_transformations",

    # Deployment
    "DeploymentManager",
]

def get_version() -> str:
    """
    Returns the core module version.

    Returns:
        str: The current version of the core module.
    """
    return __version__

def get_module_metadata() -> Dict[str, Any]:
    """
    Returns metadata about the core module.

    Returns:
        Dict[str, Any]: A dictionary containing module metadata including:
            - version: Current module version
            - author: Module maintainers
            - modules: List of available modules
            - features: List of core features
    """
    return {
        "version": __version__,
        "author": __author__,
        "modules": list(DEFAULT_MODULE_CONFIG.keys()),
        "features": [
            "Configuration Management",
            "Deployment Orchestration",
            "Resource Management",
            "Compliance Controls",
            "Metadata Management"
        ]
    }
