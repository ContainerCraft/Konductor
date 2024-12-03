# ./modules/core/__init__.py
"""
Konductor Core Module

This module provides the core functionality for the Konductor Infrastructure as Code platform.
It handles configuration management, deployment orchestration, resource management,
and compliance controls.

**Key Components**:

- **Configuration Management**: Handles configuration loading, validation, and merging.
- **Deployment Orchestration**: Manages module deployment and dependencies.
- **Resource Management**: Provides resource creation and transformation utilities.
- **Metadata Management**: Handles global metadata and tagging.
- **Git Utilities**: Provides utilities for Git repository interactions.
- **Type Definitions**: Defines core data structures and types.
- **Utilities**: Provides generic utility functions.
- **Stack Outputs**: Manages standardized stack outputs.
- **Exception Handling**: Defines custom exceptions for error handling.

**Usage**:

from modules.core import (
    initialize_pulumi,
    DeploymentManager,
    ConfigManager,
    ComplianceConfig,
    InitializationConfig,
    get_version,
    get_module_metadata,
)
"""

# Version information
__version__ = "0.0.1"
__author__ = "ContainerCraft Konductor Maintainers"

# Type exports
from .types import (
    GitInfo,
    InitializationConfig,
    ModuleDefaults,
    ModuleRegistry,
    ConfigurationValidator,
    FismaConfig,
    NistConfig,
    ScipConfig,
    ComplianceConfig,
    ModuleBase,
    StackOutputs,
    GlobalMetadata,
)

# Interfaces
from .interfaces import (
    ResourceMetadata,
    ModuleDeploymentResult,
    DeploymentContext,
    ModuleInterface,
    ResourceManagerInterface,
)

# Configuration management
from .config import (
    ensure_cache_dir,
    coerce_to_bool,
    get_module_config,
    validate_version_format,
    load_versions_from_file,
    load_versions_from_url,
    load_default_versions,
    export_results,
    validate_url,
    validate_module_config,
    merge_configurations,
    initialize_config,
    get_enabled_modules,
    DEFAULT_MODULE_CONFIG,
    ConfigManager,
)

# Deployment
from .deployment import DeploymentManager

# Exceptions
from .exceptions import (
    KonductorError,
    ModuleLoadError,
    ModuleDeploymentError,
)

# Initialization
from .initialization import initialize_pulumi

# Metadata management
from .metadata import (
    setup_global_metadata,
    MetadataSingleton,
)

# Git utilities
from .git import (
    get_latest_semver_tag,
    get_remote_url,
    sanitize_git_info,
    extract_repo_name,
    collect_git_info,
    is_valid_git_url,
)

# Utility functions
from .utils import (
    set_resource_metadata,
    generate_global_transformations,
    apply_tags,
)

# Stack outputs
from .stack_outputs import (
    get_stack_outputs,
    collect_global_metadata,
    collect_module_metadata,
    collect_compliance_outputs,
)

# Public API
__all__ = [
    # Types
    "GitInfo",
    "InitializationConfig",
    "ModuleDefaults",
    "ModuleRegistry",
    "ConfigurationValidator",
    "FismaConfig",
    "NistConfig",
    "ScipConfig",
    "ComplianceConfig",
    "ModuleBase",
    "StackOutputs",
    "GlobalMetadata",
    # Interfaces
    "ResourceMetadata",
    "ModuleDeploymentResult",
    "DeploymentContext",
    "ModuleInterface",
    "ResourceManagerInterface",
    # Configuration
    "ensure_cache_dir",
    "coerce_to_bool",
    "get_module_config",
    "validate_version_format",
    "load_versions_from_file",
    "load_versions_from_url",
    "load_default_versions",
    "export_results",
    "validate_url",
    "validate_module_config",
    "merge_configurations",
    "initialize_config",
    "get_enabled_modules",
    "DEFAULT_MODULE_CONFIG",
    "ConfigManager",
    # Deployment
    "DeploymentManager",
    # Exceptions
    "KonductorError",
    "ModuleLoadError",
    "ModuleDeploymentError",
    # Initialization
    "initialize_pulumi",
    # Metadata
    "setup_global_metadata",
    "MetadataSingleton",
    # Git utilities
    "get_latest_semver_tag",
    "get_remote_url",
    "sanitize_git_info",
    "extract_repo_name",
    "collect_git_info",
    "is_valid_git_url",
    # Utilities
    "set_resource_metadata",
    "generate_global_transformations",
    "apply_tags",
    # Stack outputs
    "get_stack_outputs",
    "collect_global_metadata",
    "collect_module_metadata",
    "collect_compliance_outputs",
]
