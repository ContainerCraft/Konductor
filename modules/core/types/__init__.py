# ./modules/core/types/__init__.py
"""
Core module types implementation.

This module defines all shared data classes, interfaces, and types used across the core and other modules.
It provides type-safe configuration structures using Pydantic models and TypedDicts, plus validation protocols.
We unify and streamline a large previously scattered codebase into a single coherent file for initial testing
before splitting into submodules.

Conventions and Requirements:
- Strict typing enforced by Pyright in strict mode.
- No `Any` type usage: replaced with `object` or more specific types.
- Pydantic models for configuration and validation.
- TypedDict for strictly typed dictionaries.
- Protocols for interfaces with clear docstrings and return annotations.
- Comprehensive docstrings for all public classes and methods.
- No broad `except Exception` blocks, except where explicitly needed to log and re-raise.
- Security and compliance considerations baked in.
- No hardcoded credentials or secrets.
- Code follows PEP 8, PEP 257, and all documented style standards.
- After verification and testing, we will refactor into a proper module structure.

This is a single large omnibus module to allow testing before final refactoring into multiple files.
"""

from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import (
    Dict, List, Optional, Union, Protocol, ClassVar, cast
)
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, validator, ConfigDict
import pulumi
from pulumi import Resource, log


# -----------------------
# Exceptions
# -----------------------
class CoreError(Exception):
    """Base exception for the core module."""
    pass


class ModuleLoadError(CoreError):
    """Exception raised when a module cannot be loaded."""
    pass


# -----------------------
# Git Metadata
# -----------------------
class GitInfo(BaseModel):
    """
    Git Repository Metadata.

    Provides structured information about the Git repository associated with the current project:
    commit hash, branch name, and remote URL.
    """
    commit_hash: str = Field(default="unknown", description="git commit hash")
    branch_name: str = Field(default="unknown", description="git branch name")
    remote_url: str = Field(default="unknown", description="git remote URL")

    def model_dump(self) -> Dict[str, str]:
        """
        Convert the GitInfo instance to a dictionary format.

        Returns:
            Dict[str, str]: Dictionary with keys 'commit', 'branch', and 'remote'.
        """
        return {
            "commit": self.commit_hash,
            "branch": self.branch_name,
            "remote": self.remote_url,
        }


# -----------------------
# Compliance Configuration
# -----------------------
class OwnershipInfo(TypedDict):
    """Owner contact information."""
    name: str
    contacts: List[str]


class AtoConfig(TypedDict):
    """ATO (Authority to Operate) configuration."""
    id: str
    authorized: str  # ISO datetime
    eol: str         # ISO datetime
    last_touch: str  # ISO datetime


class ProjectOwnership(TypedDict):
    """Project ownership structure."""
    owner: OwnershipInfo
    operations: OwnershipInfo


class ProjectProviders(TypedDict):
    """Cloud provider configuration."""
    name: List[str]
    regions: List[str]


class ProjectConfig(BaseModel):
    """Project configuration."""
    environment: str = Field(..., description="e.g., 'prod-us-west'")
    production: bool = Field(default=False)
    ownership: ProjectOwnership
    ato: AtoConfig
    providers: ProjectProviders


class FismaConfig(BaseModel):
    """FISMA compliance configuration."""
    level: str = Field(default="moderate")
    mode: str = Field(default="warn")


class NistConfig(BaseModel):
    """NIST compliance configuration."""
    auxiliary: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)


class ComplianceConfig(BaseModel):
    """
    Consolidated compliance configuration.
    This maps to the 'compliance' section of the stack configuration.
    """
    project: ProjectConfig
    fisma: FismaConfig
    nist: NistConfig

    @classmethod
    def from_pulumi_config(cls, config: pulumi.Config, timestamp: datetime) -> "ComplianceConfig":
        """
        Create ComplianceConfig from Pulumi config.

        If there's an error in loading or parsing config, returns a default config.

        Args:
            config: Pulumi configuration object
            timestamp: Current timestamp for configuration creation

        Returns:
            ComplianceConfig: Configuration instance
        """
        try:
            raw = config.get_object("compliance") or {}
            compliance_data = cast(Dict[str, object], raw)

            project_data = cast(Dict[str, object], compliance_data.get("project", {}))
            is_production = bool(project_data.get("production", False))

            ato_data = cast(Dict[str, object], project_data.get("ato", {}))
            current_time = timestamp.isoformat()

            if is_production:
                # Production must have 'authorized' date
                if "authorized" not in ato_data:
                    raise ValueError("Production environments require 'authorized' date in ATO configuration")
                authorized_date = str(ato_data["authorized"])
            else:
                authorized_date = current_time

            if "eol" in ato_data:
                eol_date = str(ato_data["eol"])
            else:
                if is_production:
                    raise ValueError("Production environments require 'eol' date in ATO configuration")
                else:
                    # Dev/non-prod gets 24h EOL from now
                    eol_date = (timestamp + timedelta(hours=24)).isoformat()

            # Ensure project data structure
            if "project" not in compliance_data:
                compliance_data["project"] = {
                    "environment": "dev",
                    "production": False,
                    "ownership": {
                        "owner": {"name": "default", "contacts": []},
                        "operations": {"name": "default", "contacts": []}
                    },
                    "ato": {
                        "id": "default",
                        "authorized": authorized_date,
                        "eol": eol_date,
                        "last_touch": current_time
                    },
                    "providers": {"name": [], "regions": []}
                }
            else:
                proj = cast(Dict[str, object], compliance_data["project"])
                proj["ato"] = {
                    "id": str(ato_data.get("id", "dev")),
                    "authorized": authorized_date,
                    "eol": eol_date,
                    "last_touch": current_time
                }

            if "fisma" not in compliance_data:
                compliance_data["fisma"] = {"level": "moderate", "mode": "warn"}

            if "nist" not in compliance_data:
                compliance_data["nist"] = {"auxiliary": [], "exceptions": []}

            return cls(**compliance_data)

        except (KeyError, ValueError) as e:
            log.error(f"Failed to load compliance config: {str(e)}")
            return cls.create_default()

    @classmethod
    def create_default(cls) -> "ComplianceConfig":
        """
        Create a default compliance configuration.

        Returns:
            ComplianceConfig: Default configuration instance
        """
        timestamp = datetime.now(timezone.utc)
        current_time = timestamp.isoformat()

        return cls(
            project=ProjectConfig(
                environment="dev",
                production=False,
                ownership={
                    "owner": {"name": "default", "contacts": []},
                    "operations": {"name": "default", "contacts": []}
                },
                ato={
                    "id": "default",
                    "authorized": current_time,
                    "eol": (timestamp + timedelta(hours=24)).isoformat(),
                    "last_touch": current_time
                },
                providers={"name": [], "regions": []}
            ),
            fisma=FismaConfig(
                level="low",
                mode="warn"
            ),
            nist=NistConfig(
                auxiliary=[],
                exceptions=[]
            )
        )

    def model_dump(self) -> Dict[str, object]:
        """Convert the model to a dictionary."""
        return {
            "project": self.project.dict(),
            "fisma": self.fisma.dict(),
            "nist": self.nist.dict()
        }


# -----------------------
# Base Resource and Config Types
# -----------------------
class ResourceBase(BaseModel):
    """
    Base for all infrastructure resources.
    Provides a minimal set of fields common to all resources.
    """
    name: str = Field(..., description="Resource name")
    urn: Optional[str] = Field(None, description="Pulumi resource identifier")
    id: Optional[str] = Field(None, description="Provider-assigned resource ID")
    metadata: Dict[str, object] = Field(
        default_factory=lambda: {
            "tags": {},
            "labels": {},
            "annotations": {},
        },
        description="Runtime resource metadata, including tags, labels, annotations."
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Resource creation timestamp"
    )


class ConfigBase(BaseModel):
    """
    Base for all configurations.
    Includes enabling/disabling a module, dependencies, and user config.
    """
    enabled: bool = Field(default=False)
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    configuration: Dict[str, object] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}}
    )


class InitializationConfig(ConfigBase):
    """
    Configuration for core module initialization.
    Provides details necessary for initializing the core module,
    including Pulumi settings, stack/project names, providers, and compliance info.
    """
    pulumi_config: Union[pulumi.Config, Dict[str, object]]
    stack_name: str
    project_name: str
    global_depends_on: List[Resource] = Field(default_factory=list)
    platform_providers: Dict[str, object] = Field(default_factory=dict)
    git_info: GitInfo = Field(default_factory=GitInfo)
    compliance_config: ComplianceConfig = Field(
        default_factory=ComplianceConfig.create_default,
        description="Compliance configuration for the deployment"
    )
    metadata: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}}
    )
    deployment_date_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    deployment_manager: Optional[object] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @validator("configuration")
    def validate_configuration(cls, v: Dict[str, object]) -> Dict[str, object]:
        """Validate that all configuration values are dictionaries."""
        if not all(isinstance(config, dict) for config in v.values()):
            raise ValueError("All configurations must be dictionaries")
        return v


class ModuleRegistry(ConfigBase):
    """
    Module registration information.
    """
    name: str
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class ModuleBase(BaseModel):
    """
    Base class for all modules.
    Represents a deployable unit of infrastructure.
    """
    name: str = Field(..., description="Module name")
    enabled: bool = Field(default=False, description="Whether module is enabled")
    parent: Optional[str] = Field(None, description="Parent resource name")
    dependencies: List[str] = Field(default_factory=list, description="Module dependencies")
    config: Dict[str, object] = Field(default_factory=dict, description="Module configuration")
    metadata: Dict[str, object] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}},
        description="Module metadata"
    )


# -----------------------
# Deployment Result and Interfaces
# -----------------------
class ModuleDeploymentResult(BaseModel):
    """
    Results from a module deployment operation.

    Attributes:
        success: Whether the deployment was successful
        config: List of ResourceBase configurations for sharing
        compliance: List of compliance/tracing info
        resources: Dictionary of resources created or updated
        errors: List of error messages if any occurred
        metadata: Additional deployment metadata
    """
    success: bool
    config: List[ResourceBase] = Field(default_factory=list)
    compliance: List[str] = Field(default_factory=list)
    resources: Dict[str, object] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)


class DeploymentContext(Protocol):
    """Protocol defining the deployment context interface."""

    def get_config(self) -> ConfigBase:
        """
        Retrieve the configuration for the deployment.

        Returns:
            ConfigBase: The configuration model for this deployment context.
        """
        ...

    def deploy(self) -> ModuleDeploymentResult:
        """
        Execute the deployment and return results.

        Returns:
            ModuleDeploymentResult: The result of the deployment process.
        """
        ...


class ModuleInterface(Protocol):
    """
    Module interface defining lifecycle and validation methods.
    """

    def validate_config(self, config: ConfigBase) -> List[str]:
        """
        Validate module configuration and return a list of errors if any.

        Args:
            config (ConfigBase): The configuration to validate.

        Returns:
            List[str]: A list of validation error messages, empty if valid.
        """
        ...

    def validate_resources(self, resources: List[ResourceBase]) -> List[str]:
        """
        Validate module resources and return a list of errors if any.

        Args:
            resources (List[ResourceBase]): The resources to validate.

        Returns:
            List[str]: A list of validation error messages, empty if valid.
        """
        ...

    def pre_deploy_check(self) -> List[str]:
        """
        Run checks before deploying resources.

        Returns:
            List[str]: A list of pre-deployment error messages, empty if valid.
        """
        ...

    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult:
        """
        Deploy the module using the provided deployment context.

        Args:
            ctx (DeploymentContext): The deployment context.

        Returns:
            ModuleDeploymentResult: The result of the module deployment.
        """
        ...

    def post_deploy_validation(self, result: ModuleDeploymentResult) -> List[str]:
        """
        Validate the deployment result after resources are created.

        Args:
            result (ModuleDeploymentResult): The result to validate.

        Returns:
            List[str]: A list of post-deployment validation errors, empty if valid.
        """
        ...

    def get_dependencies(self) -> List[str]:
        """
        Return a list of module dependencies.

        Returns:
            List[str]: The names of dependent modules.
        """
        ...


# -----------------------
# Metadata Singleton
# -----------------------
class MetadataSingleton:
    """
    Global metadata thread-safe singleton class.
    Provides a centralized store for all cross-module metadata.
    """

    _instance: Optional["MetadataSingleton"] = None
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls) -> "MetadataSingleton":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()  # type: ignore
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._global_tags: Dict[str, str] = {}
            self._global_labels: Dict[str, str] = {}
            self._global_annotations: Dict[str, str] = {}
            self._git_metadata: Dict[str, object] = {}
            self._modules_metadata: Dict[str, Dict[str, object]] = {}
            self._initialized = True

    @property
    def global_tags(self) -> Dict[str, str]:
        with self._lock:
            return self._global_tags.copy()

    @property
    def global_labels(self) -> Dict[str, str]:
        with self._lock:
            return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        with self._lock:
            return self._global_annotations.copy()

    @property
    def git_metadata(self) -> Dict[str, object]:
        with self._lock:
            return self._git_metadata.copy()

    @property
    def modules_metadata(self) -> Dict[str, Dict[str, object]]:
        with self._lock:
            return self._modules_metadata.copy()

    def set_tags(self, tags: Dict[str, str]) -> None:
        with self._lock:
            self._global_tags.update(tags)

    def set_labels(self, labels: Dict[str, str]) -> None:
        with self._lock:
            self._global_labels.update(labels)

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        with self._lock:
            self._global_annotations.update(annotations)

    def set_git_metadata(self, metadata: Dict[str, str]) -> None:
        with self._lock:
            self._git_metadata.update(metadata)

    def set_module_metadata(self, module_name: str, metadata: Dict[str, object]) -> None:
        with self._lock:
            if module_name not in self._modules_metadata:
                self._modules_metadata[module_name] = {}
            self._modules_metadata[module_name].update(metadata)

    def get_module_metadata(self, module_name: str) -> Dict[str, object]:
        with self._lock:
            return self._modules_metadata.get(module_name, {}).copy()


# -----------------------
# InitConfig Protocol (for setup_global_metadata)
# -----------------------
class InitConfig(Protocol):
    """
    Protocol for initial configuration used when setting up global metadata.
    """
    project_name: str
    stack_name: str
    git_info: GitInfo
    metadata: Dict[str, Dict[str, str]]


# -----------------------
# Setup Global Metadata
# -----------------------
def setup_global_metadata(init_config: InitConfig) -> None:
    """
    Initialize global metadata for resources using the provided InitConfig.

    This sets global tags, labels, annotations, and git metadata in the MetadataSingleton.
    """
    try:
        metadata = MetadataSingleton()

        git_info = init_config.git_info.model_dump()
        git_labels = {
            "git.commit": git_info["commit"],
            "git.branch": git_info["branch"],
            "git.repository": git_info["remote"],
        }

        base_metadata = {
            "managed-by": f"pulumi-{init_config.project_name}-{init_config.stack_name}",
            "project": init_config.project_name,
            "stack": init_config.stack_name,
            "git": git_info,
        }

        base_tags = {
            **base_metadata,
            **init_config.metadata.get("tags", {}),
        }

        base_labels = {
            **base_metadata,
            **init_config.metadata.get("labels", {}),
        }

        base_annotations = {
            **base_metadata,
            **init_config.metadata.get("annotations", {}),
        }

        all_labels = {
            **base_labels,
            **git_labels,
            **(init_config.metadata.get("labels", {})),
        }

        metadata.set_tags({k: str(v) for k, v in base_tags.items()})
        metadata.set_labels({k: str(v) for k, v in all_labels.items()})
        metadata.set_annotations({k: str(v) for k, v in base_annotations.items()})
        metadata.set_git_metadata({k: str(v) for k, v in git_info.items()})

        log.info("Global metadata initialized successfully")
    except Exception as e:
        log.error(f"Failed to setup global metadata: {e}")
        raise


# -----------------------
# Configuration Management
# -----------------------
class ConfigManager:
    """
    Configuration Management Class
    Retrieves and caches Pulumi configuration for modules.
    """

    def __init__(self) -> None:
        self.pulumi_config = pulumi.Config()
        self._config_cache: Optional[Dict[str, object]] = None
        self._module_configs: Dict[str, Dict[str, object]] = {}

    def get_config(self) -> Dict[str, object]:
        """Get the full configuration from Pulumi stack config."""
        if self._config_cache is None:
            raw_config: Dict[str, object] = {}
            for module_name in ["aws", "kubernetes"]:
                try:
                    module_cfg = pulumi.Config(module_name).get_object("") or {}
                    raw_config[module_name] = module_cfg
                except KeyError as e:
                    log.debug(f"No config found for module {module_name}: {e}")

            self._config_cache = raw_config
            log.debug(f"Loaded config: {raw_config}")

        return cast(Dict[str, object], self._config_cache)

    def get_module_config(self, module_name: str) -> Dict[str, object]:
        """Get configuration for a specific module."""
        if module_name in self._module_configs:
            return self._module_configs[module_name]

        config = self.get_config()
        module_config = cast(Dict[str, object], config.get(module_name, {}))

        self._module_configs[module_name] = module_config
        log.debug(f"Module {module_name} config: {module_config}")
        return module_config

    def get_enabled_modules(self) -> List[str]:
        """Get list of enabled modules."""
        enabled_modules: List[str] = []
        config = self.get_config()

        for module_name in ["aws", "kubernetes"]:
            module_config = cast(Dict[str, object], config.get(module_name, {}))
            if bool(module_config.get("enabled", False)):
                enabled_modules.append(module_name)
                log.info(f"Module {module_name} is enabled")

        log.info(f"Enabled modules: {enabled_modules}")
        return enabled_modules


# -----------------------
# Global Metadata and Stack Config
# -----------------------
class GlobalMetadata(BaseModel):
    """
    Global metadata structure.
    Used for top-level stack outputs metadata.
    """
    tags: Dict[str, str] = Field(default_factory=dict, description="Global public cloud resource tags")
    labels: Dict[str, str] = Field(default_factory=dict, description="Global Kubernetes labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Global Kubernetes annotations")


class SourceRepository(BaseModel):
    """Source repository information."""
    branch: str
    commit: str
    remote: str
    tag: Optional[str] = None


class StackConfig(BaseModel):
    """
    Root stack configuration mapping.
    """
    compliance: ComplianceConfig
    metadata: GlobalMetadata
    source_repository: SourceRepository


class StackOutputs(BaseModel):
    """
    Complete stack outputs structure.
    """
    stack: StackConfig
    secrets: Optional[Dict[str, object]] = Field(
        default=None,
        description="Sensitive information like credentials or tokens"
    )


class ModuleDefaults(BaseModel):
    """
    Default configuration for modules.
    """
    enabled: bool = Field(default=False, description="Whether the module is enabled")
    config: Dict[str, object] = Field(default_factory=dict, description="Module-specific configuration")


class ResourceMetadata(ResourceBase):
    """
    Resource metadata structure extending ResourceBase.
    Adds tags, labels, annotations, and timestamps.
    """
    tags: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# -----------------------
# Public API (exports)
# -----------------------
__all__ = [
    "CoreError",
    "ModuleLoadError",
    "GitInfo",
    "ProjectConfig",
    "FismaConfig",
    "NistConfig",
    "ComplianceConfig",
    "OwnershipInfo",
    "AtoConfig",
    "ProjectOwnership",
    "ProjectProviders",
    "ResourceBase",
    "ConfigBase",
    "InitializationConfig",
    "ModuleRegistry",
    "ModuleBase",
    "ModuleDeploymentResult",
    "DeploymentContext",
    "ModuleInterface",
    "MetadataSingleton",
    "InitConfig",
    "setup_global_metadata",
    "ConfigManager",
    "GlobalMetadata",
    "SourceRepository",
    "StackConfig",
    "StackOutputs",
    "ModuleDefaults",
    "ResourceMetadata",
]
