# ./modules/core/types/base.py
"""
Core module base types implementation.

This module provides foundational types and interfaces for the core module.
It includes data structures for Git metadata, compliance configurations,
initialization settings, and module management. These types are essential
for ensuring consistent configuration and deployment across the platform.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, ConfigDict, validator
import pulumi
from pulumi import Resource

from .compliance import ComplianceConfig


class GitInfo(BaseModel):
    """
    Git Repository Metadata.

    This class provides structured information about the Git repository
    associated with the current project. It includes details such as the
    commit hash, branch name, and remote URL.

    Attributes:
        commit_hash (str): The current commit hash of the repository.
        branch_name (str): The current branch name of the repository.
        remote_url (str): The remote URL of the repository.
    """

    commit_hash: str = Field(default="unknown", description="Current git commit hash")
    branch_name: str = Field(default="unknown", description="Current git branch name")
    remote_url: str = Field(default="unknown", description="Current git remote URL")

    def model_dump(self) -> Dict[str, Any]:
        """
        Convert the GitInfo instance to a dictionary format.

        Returns:
            Dict[str, Any]: Dictionary of git commit hash, branch name, and remote URL.
        """
        return {
            "commit": self.commit_hash,
            "branch": self.branch_name,
            "remote": self.remote_url,
        }


class ResourceBase(BaseModel):
    """Base for all infrastructure resources."""
    name: str = Field(..., description="Resource name")
    urn: Optional[str] = Field(None, description="Pulumi resource identifier")
    id: Optional[str] = Field(None, description="Provider-assigned resource ID")
    # Metadata for resource tags, labels, and annotations.
    metadata: Dict[str, Any] = Field(
        description="Runtime resource metadata",
        default_factory=lambda: {
            "tags": {},
            "labels": {},
            "annotations": {},
        }
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ConfigBase(BaseModel):
    """
    Base for all configurations.

    This class provides a base for all configurations, including
    enabling/disabling a module, setting its version, and defining
    dependencies and configurations.

    Attributes:
        enabled (bool): Whether the module is enabled.
        version (Optional[str]): The version of the module.
        parent (Optional[str]): The parent module name, cannot be set in both parent and dependencies.
        dependencies (List[str]): A list of module dependencies, cannot be set in both parent and dependencies.
        configuration (Dict[str, Any]): Configuration propagated from Pulumi Stack config settings.
        metadata (Dict[str, Any]): Metadata including resource tags, labels, and annotations.
    """
    enabled: bool = Field(default=False)
    version: Optional[str] = None
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}}
    )


class InitializationConfig(ConfigBase):
    """
    Configuration for core module initialization.

    This class provides configuration details necessary for initializing the core module,
    including Pulumi settings, project and stack names, version information, and more.

    Attributes:
        pulumi_config (Union[pulumi.Config, Any]): The Pulumi configuration object.
        stack_name (str): The name of the stack.
        project_name (str): The name of the project.
        global_depends_on (List[Resource]): List of global dependencies.
        platform_providers (Dict[str, Any]): Cloud provider (e.g. AWS, GCP, Azure, Kubernetes, OpenStack, etc.) configurations.
        git_info (GitInfo): Git repository metadata.
        compliance_config (ComplianceConfig): Compliance configuration settings.
        metadata (Dict[str, Dict[str, str]]): Metadata including labels and annotations.
        deployment_date_time (str): The date and time of deployment.
        deployment_manager (Optional[Any]): The deployment manager instance.
    """

    pulumi_config: Union[pulumi.Config, Any]
    stack_name: str
    project_name: str
    global_depends_on: List[Resource] = Field(default_factory=list)
    platform_providers: Dict[str, Any] = Field(default_factory=dict)
    git_info: GitInfo = Field(default_factory=GitInfo)
    compliance_config: ComplianceConfig = Field(default_factory=ComplianceConfig)
    metadata: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}}
    )
    deployment_date_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    deployment_manager: Optional[Any] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @validator("configuration")
    def validate_configuration(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate module configurations."""
        if not all(isinstance(config, dict) for config in v.values()):
            raise ValueError("All configurations must be dictionaries")
        return v


class ModuleRegistry(ConfigBase):
    """
    Module registration information.

    This class holds information about registered modules, including the
    module's name, version, and any dependencies it may have.

    Attributes:
        name (str): The name of the module.
        version (Optional[str]): The version of the module.
        dependencies (List[str]): A list of module dependencies.
    """

    name: str
    version: Optional[str] = None
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class ModuleBase(BaseModel):
    """
    Base class for all modules.

    Provides common functionality and type safety for module implementations.
    Modules represent deployable units of infrastructure.

    Attributes:
        name (str): The name of the module.
        version (Optional[str]): The version of the module.
        enabled (bool): Whether the module is enabled.
        parent (Optional[str]): The parent module name, cannot be set in both parent and dependencies.
        dependencies (List[str]): A list of module dependencies, cannot be set in both parent and dependencies.
        config (Dict[str, Any]): Configuration propagated from Pulumi Stack config settings.
        metadata (Dict[str, Any]): Metadata including resource tags, labels, and annotations.
    """
    name: str = Field(..., description="Module name")
    version: Optional[str] = Field(None, description="Module version")
    enabled: bool = Field(default=False, description="Whether module is enabled")
    parent: Optional[str] = Field(None, description="Parent resource name, cannot be set in both parent and dependencies")
    dependencies: List[str] = Field(default_factory=list, description="Module dependencies, cannot be set in both parent and dependencies")
    config: Dict[str, Any] = Field(default_factory=dict, description="Module configuration")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}},
        description="Module metadata"
    )
