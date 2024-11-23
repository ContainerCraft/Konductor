# ../konductor/modules/core/types.py

"""
Types and Data Structures Module

This module defines all shared data classes and types used across all modules.
It provides type-safe configuration structures using Pydantic models and TypedDict.
"""

from typing import Dict, List, Optional, TypeVar, Union, TypedDict, Any, Protocol
from pydantic import BaseModel, Field, ValidationError
from dataclasses import dataclass, field
import pulumi
import pulumi_kubernetes as k8s
from pulumi import Resource, Output
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

# Type variables
T = TypeVar('T')
MetadataType = Union[Dict[str, Any], ObjectMetaArgs, Output[Dict[str, Any]]]
ResourceType = TypeVar('ResourceType', bound=Resource)

class GitInfo(BaseModel):
    commit_hash: str = 'unknown'
    branch_name: str = 'unknown'
    remote_url: str = 'unknown'

class InitializationConfig(BaseModel):
    """
    Configuration for core module initialization.

    This class encapsulates all necessary configuration and state needed
    for initializing and managing the core module components.

    Attributes:
        pulumi_config: Pulumi configuration object
        stack_name: Name of the current Pulumi stack
        project_name: Name of the Pulumi project
        default_versions: Default versions for all modules
        versions: Current versions of deployed modules
        configurations: Module-specific configurations
        global_depends_on: Global resource dependencies
        kubernetes_provider: Kubernetes provider instance
        git_info: Git repository information
        compliance_config: Compliance configuration
        metadata: Resource metadata
    """
    pulumi_config: pulumi.Config
    stack_name: str
    project_name: str
    default_versions: Dict[str, Any]
    versions: Dict[str, str] = Field(default_factory=dict)
    configurations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    global_depends_on: List[Resource] = Field(default_factory=list)
    kubernetes_provider: Optional[k8s.Provider] = None
    git_info: GitInfo = GitInfo()
    compliance_config: Any = Field(default_factory=dict)  # Placeholder for compliance config
    metadata: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}}
    )

    @property
    def config(self) -> Any:
        """
        Provides backwards compatibility for config access.
        Returns the pulumi_config object.
        """
        return self.pulumi_config

    class Config:
        arbitrary_types_allowed = True

class ModuleDefaults(TypedDict):
    """
    Default configuration for modules.

    Attributes:
        enabled: Whether the module is enabled by default
        version: Optional default version
        config: Additional module configuration
    """
    enabled: bool
    version: Optional[str]
    config: Dict[str, Any]

class CustomType:
    def __init__(self, value: str):
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomType':
        return cls(value=data["value"])

class ModuleRegistry(BaseModel):
    name: str
    version: Optional[str] = None
    dependencies: List[str] = []

    def to_dict(self) -> dict:
        return self.model_dump()

class ConfigurationValidator:
    """Validates module configurations against their schemas."""

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry

    def validate_module_config(
        self,
        module_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Validates module configuration.
        Returns list of validation errors.
        """
        errors = []
        module = self.registry.get_module(module_name)
        if not module:
            errors.append(f"Module {module_name} not registered")
            return errors

        try:
            module.validate_config(config)
        except ValidationError as e:
            errors.extend(str(error) for error in e.errors())
        return errors

@dataclass
class FismaConfig:
    enabled: bool = False
    level: Optional[str] = None
    ato: Dict[str, str] = field(default_factory=dict)

@dataclass
class NistConfig:
    enabled: bool = False
    controls: List[str] = field(default_factory=list)
    auxiliary: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)

@dataclass
class ScipConfig:
    environment: Optional[str] = None
    ownership: Dict[str, Any] = field(default_factory=dict)
    provider: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceConfig:
    fisma: FismaConfig = field(default_factory=FismaConfig)
    nist: NistConfig = field(default_factory=NistConfig)
    scip: ScipConfig = field(default_factory=ScipConfig)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'ComplianceConfig':
        """
        Merges user-provided compliance configuration with default configuration.

        Args:
            user_config (Dict[str, Any]): The user-provided compliance configuration.

        Returns:
            ComplianceConfig: The merged compliance configuration object.
        """
        default_config = ComplianceConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                nested_config = getattr(default_config, key)
                for nested_key, nested_value in value.items():
                    if hasattr(nested_config, nested_key):
                        setattr(nested_config, nested_key, nested_value)
                    else:
                        pulumi.log.warn(f"Unknown key '{nested_key}' in compliance.{key}")
            else:
                pulumi.log.warn(f"Unknown compliance configuration key: {key}")
        return default_config

class ModuleBase(Protocol):
    """
    Base class for all infrastructure modules.
    Provides a common interface for configuration and deployment.
    """
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate the module's configuration."""
        ...

    def deploy(self, context: Any) -> Any:
        """Deploy the module using the provided context."""
        ...

    def get_dependencies(self) -> List[str]:
        """Return a list of module dependencies."""
        ...

class StackOutputs(TypedDict):
    """Stack outputs structure.

    Attributes:
        compliance: Compliance metadata and controls including general metadata, git_info, and compliance controls
        config: Consolidated stack configuration output useful for business intelligence and down stream deployment automation
        k8s_app_versions: Versions of deployed Kubernetes components
    """
    compliance: Dict[str, Any]
    config: Dict[str, Any]
    k8s_app_versions: Dict[str, str]
