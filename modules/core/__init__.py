"""
Konductor Core Module

This module provides the core functionality for the Konductor Infrastructure as Code platform.
It handles configuration management, deployment orchestration, resource management,
and compliance controls.

Key Components:
- Configuration Management
- Deployment Orchestration
- Resource Helpers
- Metadata Management
- Type Definitions

Usage:
    from pulumi.core import (
        initialize_pulumi,
        deploy_modules,
        ComplianceConfig,
        InitializationConfig
    )
"""

from typing import Dict, List, Any, Optional

# Version information
__version__ = "0.1.0"
__author__ = "ContainerCraft Konductor Maintainers"

# Type exports
from .types import (
    ComplianceConfig,
    InitializationConfig,
    ModuleBase,
    ModuleDefaults,
    ModuleDeploymentResult,
    ResourceMetadata,
    NamespaceConfig,
    FismaConfig,
    NistConfig,
    ScipConfig,
)

# Configuration management
from .config import (
    get_module_config,
    load_default_versions,
    export_results,
    validate_module_config,
    initialize_config,
    merge_configurations,
)

# Deployment management
from .deployment import (
    initialize_pulumi,
    deploy_modules,
    DeploymentManager,
)

# Resource helpers
from .resource_helpers import (
    create_namespace,
    create_custom_resource,
    create_helm_release,
    create_secret,
    create_config_file,
)

# Metadata management
from .metadata import (
    collect_git_info,
    generate_git_labels,
    generate_git_annotations,
    generate_compliance_labels,
    generate_compliance_annotations,
    set_global_labels,
    set_global_annotations,
    get_global_labels,
    get_global_annotations,
)

# Utility functions
from .utils import (
    set_resource_metadata,
    generate_global_transformations,
    get_latest_helm_chart_version,
    wait_for_crds,
)

# Default module configuration
DEFAULT_MODULE_CONFIG: Dict[str, ModuleDefaults] = {
    "aws": {"enabled": False, "version": None, "config": {}},
    "cert_manager": {"enabled": True, "version": None, "config": {}},
    "kubevirt": {"enabled": True, "version": None, "config": {}},
    "multus": {"enabled": True, "version": None, "config": {}},
    "hostpath_provisioner": {"enabled": True, "version": None, "config": {}},
    "containerized_data_importer": {"enabled": True, "version": None, "config": {}},
    "prometheus": {"enabled": True, "version": None, "config": {}}
}

# Public API
__all__ = [
    # Types
    "ComplianceConfig",
    "InitializationConfig",
    "ModuleBase",
    "ModuleDefaults",
    "ModuleDeploymentResult",
    "ResourceMetadata",
    "NamespaceConfig",
    "FismaConfig",
    "NistConfig",
    "ScipConfig",

    # Configuration
    "get_module_config",
    "load_default_versions",
    "export_results",
    "validate_module_config",
    "initialize_config",
    "merge_configurations",
    "DEFAULT_MODULE_CONFIG",

    # Deployment
    "initialize_pulumi",
    "deploy_modules",
    "DeploymentManager",

    # Resources
    "create_namespace",
    "create_custom_resource",
    "create_helm_release",
    "create_secret",
    "create_config_file",

    # Metadata
    "collect_git_info",
    "generate_git_labels",
    "generate_git_annotations",
    "generate_compliance_labels",
    "generate_compliance_annotations",
    "set_global_labels",
    "set_global_annotations",
    "get_global_labels",
    "get_global_annotations",

    # Utilities
    "set_resource_metadata",
    "generate_global_transformations",
    "get_latest_helm_chart_version",
    "wait_for_crds",
]

def get_version() -> str:
    """Returns the core module version."""
    return __version__

def get_module_metadata() -> Dict[str, Any]:
    """Returns metadata about the core module."""
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
