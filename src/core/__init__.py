# ./modules/core/__init__.py
"""
Konductor Core Module

This module provides the core functionality for the Konductor Infrastructure as Code
platform. It handles configuration management, deployment orchestration, resource
management, and compliance controls.
"""

from .types import (
    CoreError,
    ModuleLoadError,
    ModuleDeploymentError,
    CommonMetadataFields,
    GitInfo,
    OwnershipInfo,
    AtoConfig,
    ProjectOwnership,
    ScipConfig,
    FismaConfig,
    NistConfig,
    ComplianceConfig,
    BaseConfigModel,
    InitializationConfig,
    ModuleRegistry,
    ModuleBase,
    ResourceModel,
    ModuleDeploymentResult,
    DeploymentContext,
    ModuleInterface,
    MetadataSingleton,
    InitConfig,
    setup_global_metadata,
    GlobalMetadata,
    SourceRepository,
    StackConfig,
    StackOutputs,
    ModuleDefaults,
)

from .config import (
    ConfigManager,
    validate_module_config,
    merge_configurations,
    export_results,
    get_stack_outputs,
)

from .deployment import DeploymentManager
from .initialization import initialize_pulumi
from .metadata import export_compliance_metadata

__all__ = [
    # Core Types
    "CoreError",
    "ModuleLoadError",
    "ModuleDeploymentError",
    "CommonMetadataFields",
    "GitInfo",
    "OwnershipInfo",
    "AtoConfig",
    "ProjectOwnership",
    "ScipConfig",
    "FismaConfig",
    "NistConfig",
    "ComplianceConfig",
    "BaseConfigModel",
    "InitializationConfig",
    "ModuleRegistry",
    "ModuleBase",
    "ResourceModel",
    "ModuleDeploymentResult",
    "DeploymentContext",
    "ModuleInterface",
    "MetadataSingleton",
    "InitConfig",
    "GlobalMetadata",
    "SourceRepository",
    "StackConfig",
    "StackOutputs",
    "ModuleDefaults",

    # Core Functions and Classes
    "setup_global_metadata",
    "ConfigManager",
    "DeploymentManager",
    "validate_module_config",
    "merge_configurations",
    "export_results",
    "get_stack_outputs",
    "initialize_pulumi",
    "export_compliance_metadata",
]
