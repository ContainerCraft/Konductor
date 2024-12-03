# ../konductor/modules/core/types.py

"""
Types and Data Structures Module

This module defines all shared data classes and types used across all modules.
It provides type-safe configuration structures using Pydantic models and TypedDict.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, TypeVar, Union, TypedDict, Any, Protocol
from pydantic import BaseModel, Field, ConfigDict
import pulumi
import pulumi_kubernetes as k8s
from pulumi import Resource, Output
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

from .git_types import GitInfo
from .compliance_types import ComplianceConfig

# Type variables
T = TypeVar("T")
MetadataType = Union[Dict[str, Any], ObjectMetaArgs, Output[Dict[str, Any]]]
ResourceType = TypeVar("ResourceType", bound=Resource)


class ConfigurationValidator(Protocol):
    """Protocol for configuration validation."""

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """
        Validates configuration and returns list of validation errors.
        Empty list means validation passed.
        """
        ...


class FismaConfig(TypedDict):
    """FISMA compliance configuration."""

    enabled: bool
    level: str
    ato: Dict[str, str]


class NistConfig(TypedDict):
    """NIST compliance configuration."""

    enabled: bool
    controls: List[str]
    auxiliary: List[str]
    exceptions: List[str]


class ScipConfig(TypedDict):
    """SCIP compliance configuration."""

    environment: str
    provider: Dict[str, Any]
    ownership: Dict[str, Any]


class InitializationConfig(BaseModel):
    """Configuration for core module initialization."""

    pulumi_config: Union[pulumi.Config, Any]
    stack_name: str
    project_name: str
    default_versions: Dict[str, Any]
    versions: Dict[str, str] = Field(default_factory=dict)
    configurations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    global_depends_on: List[Resource] = Field(default_factory=list)
    kubernetes_provider: Optional[k8s.Provider] = None
    git_info: GitInfo = Field(default_factory=GitInfo)
    compliance_config: ComplianceConfig = Field(default_factory=ComplianceConfig)
    metadata: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {"labels": {}, "annotations": {}})
    deployment_date_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ModuleDefaults(TypedDict):
    """Default configuration for modules."""

    enabled: bool
    version: Optional[str]
    config: Dict[str, Any]


class ModuleRegistry(BaseModel):
    """Module registration information."""

    name: str
    version: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class StackOutputs(TypedDict):
    """Stack outputs structure."""

    compliance: Dict[str, Any]
    config: Dict[str, Any]
    k8s_app_versions: Dict[str, str]


class GlobalMetadata(TypedDict):
    """Global metadata structure."""

    project_name: str
    stack_name: str
    versions: Dict[str, str]
    git_commit: str
    git_branch: str
    git_remote_url: str


class ModuleBase(Protocol):
    """Base interface for all modules."""

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate module configuration."""
        ...

    def deploy(self, context: Any) -> Any:
        """Deploy module resources."""
        ...

    def get_dependencies(self) -> List[str]:
        """Get module dependencies."""
        ...
