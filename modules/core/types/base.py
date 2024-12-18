# ./modules/core/types/__init__.py
"""
Core module types implementation (revision07).

This revision reduces duplication (DRY) by:

- Introducing a shared `CommonMetadataFields` model for tags, labels, annotations.
- Unifying repeated fields in configuration-related classes into a common base model (`BaseConfigModel`).
- Removing redundant `ResourceBase` in favor of a single `ResourceModel` that includes all needed resource fields.
- Ensuring that all attributes from the previous revision remain present but organized more coherently.

Conventions and Requirements:
- Strict typing with Pyright in strict mode.
- No `Any` type usage: replaced with `object` or more specific types.
- Pydantic models for validation and TypedDict where appropriate.
- Clear docstrings and alignment with Pulumi IaC best practices.
- No broad `except Exception` unless re-raised after logging.
- Security, compliance, and maintainability baked in.
- No hardcoded credentials or secrets.
- Follow PEP 8, PEP 257, and all style/documentation standards.

This is still a large omnibus module for testing before splitting into submodules.
"""

from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Dict, List, Optional, Union, Protocol, ClassVar, cast
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, validator, ConfigDict
import pulumi
from pulumi import Resource, log


# -----------------------
# Exceptions
# -----------------------
class CoreError(Exception):
    """Base exception for the core module errors."""

    pass


class ModuleLoadError(CoreError):
    """Exception raised when a module cannot be loaded."""

    pass


# -----------------------
# Common Metadata Fields
# -----------------------
class CommonMetadataFields(BaseModel):
    """
    Common metadata fields used repeatedly across multiple classes.
    Provides a standard structure for tags, labels, and annotations.

    Attributes:
        tags: Dict of key-value pairs for resource tagging.
        labels: Dict of key-value pairs for labeling (e.g., Kubernetes labels).
        annotations: Dict of key-value pairs for annotations.
    """

    tags: Dict[str, str] = Field(default_factory=dict, description="Key-value tags for resources.")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value labels for resources.")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Key-value annotations for resources.")


# -----------------------
# Git Metadata
# -----------------------
class GitInfo(BaseModel):
    """
    Git Repository Metadata.
    Provides commit hash, branch name, and remote URL of the current project.

    Default values are "unk" to indicate unknown state if not provided.

    Attributes:
        commit_hash: Current git commit hash
        branch_name: Current git branch name
        remote_url: Current git remote URL
        release_tag: Current git release tag if current commit is a valid semver tag
    """

    commit_hash: str = Field(default="unk", description="Git commit hash")
    branch_name: str = Field(default="unk", description="Git branch name")
    remote_url: str = Field(default="unk", description="Git remote URL")
    release_tag: Optional[str] = Field(default=None, description="Git release tag")

    def model_dump(self) -> Dict[str, str]:
        """Return a dict with commit, branch, and remote fields."""
        return {
            "commit": self.commit_hash,
            "branch": self.branch_name,
            "remote": self.remote_url,
            "tag": self.release_tag,
        }


# -----------------------
# Compliance Configuration
# -----------------------
class OwnershipInfo(TypedDict):
    """Owner contact information."""

    name: str
    contacts: List[str]


class AtoConfig(TypedDict):
    """ATO (Authority to Operate) configuration with required timestamps (ISO)."""

    id: str
    authorized: str  # ISO datetime
    eol: str  # ISO datetime
    last_touch: str  # ISO datetime


class ProjectOwnership(TypedDict):
    """Project ownership structure with owner and operations info."""

    owner: OwnershipInfo
    operations: OwnershipInfo


class StackConfig(BaseModel):
    """
    Pulumi stack configuration.
    Defines environment, production flag, ownership, and ATO details.
    """

    environment: str = Field(..., description="Arbitrary environment name, e.g. 'prod-us-west'")
    production: bool = Field(default=False, description="Is this a production environment?")
    ownership: ProjectOwnership
    ato: AtoConfig


class FismaConfig(BaseModel):
    """
    FISMA compliance configuration.
    """

    level: str = Field(default="moderate", description="FISMA compliance level: 'low', 'moderate', or 'high'")
    mode: str = Field(default="warn", description="FISMA compliance mode: 'disabled', 'warn', or 'enforcing'")


class NistConfig(BaseModel):
    """
    NIST compliance configuration.
    """

    auxiliary: List[str] = Field(default_factory=list, description="Enabled auxiliary NIST controls.")
    exceptions: List[str] = Field(default_factory=list, description="Disabled NIST control exceptions.")


class ComplianceConfig(BaseModel):
    """
    Consolidated compliance configuration mapping to 'compliance' in stack config.
    Includes Project, FISMA, and NIST configurations.
    """

    project: StackConfig
    fisma: FismaConfig
    nist: NistConfig

    @classmethod
    def from_pulumi_config(cls, config: pulumi.Config, timestamp: datetime) -> "ComplianceConfig":
        """
        Instantiate ComplianceConfig from Pulumi config.
        If production, authorized and eol dates must be present; otherwise defaults are used.
        """
        try:
            raw = config.get_object("compliance") or {}
            compliance_data = cast(Dict[str, object], raw)

            project_data = cast(Dict[str, object], compliance_data.get("project", {}))
            is_production = bool(project_data.get("production", False))

            ato_data = cast(Dict[str, object], project_data.get("ato", {}))
            current_time = timestamp.isoformat()

            if is_production and "authorized" not in ato_data:
                raise ValueError("Production environments require 'authorized' date in ATO configuration")

            authorized_date = str(ato_data.get("authorized", current_time))
            eol_date = str(ato_data.get("eol", (timestamp + timedelta(hours=24)).isoformat()))

            # Ensure project structure
            if "project" not in compliance_data:
                compliance_data["project"] = {
                    "environment": "dev",
                    "production": False,
                    "ownership": {
                        "owner": {"name": "default", "contacts": []},
                        "operations": {"name": "default", "contacts": []},
                    },
                    "ato": {
                        "id": "default",
                        "authorized": authorized_date,
                        "eol": eol_date,
                        "last_touch": current_time,
                    },
                }
            else:
                proj = cast(Dict[str, object], compliance_data["project"])
                proj["ato"] = {
                    "id": str(ato_data.get("id", "dev")),
                    "authorized": authorized_date,
                    "eol": eol_date,
                    "last_touch": current_time,
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
        Create a default compliance configuration for non-production dev environment.
        """
        timestamp = datetime.now(timezone.utc)
        current_time = timestamp.isoformat()

        return cls(
            project=StackConfig(
                environment="dev",
                production=False,
                ownership={
                    "owner": {"name": "default", "contacts": []},
                    "operations": {"name": "default", "contacts": []},
                },
                ato={
                    "id": "default",
                    "authorized": current_time,
                    "eol": (timestamp + timedelta(hours=24)).isoformat(),
                    "last_touch": current_time,
                },
            ),
            fisma=FismaConfig(level="low", mode="warn"),
            nist=NistConfig(auxiliary=[], exceptions=[]),
        )


# -----------------------
# Configuration Base Models
# -----------------------
class BaseConfigModel(BaseModel):
    """
    Base configuration model providing common fields:
    - enabled: Whether the module or config is active
    - parent: Optional parent identifier
    - dependencies: List of dependencies
    - configuration: Arbitrary configuration dictionary
    - metadata: CommonMetadataFields for tags, labels, annotations
    """

    enabled: bool = Field(default=False)
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    configuration: Dict[str, object] = Field(default_factory=dict)
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)


class InitializationConfig(BaseConfigModel):
    """
    Configuration for core module initialization.
    Adds fields necessary for stack/project initialization, compliance, and git info.
    """

    pulumi_config: Union[pulumi.Config, Dict[str, object]]
    stack_name: str
    project_name: str
    global_depends_on: List[Resource] = Field(default_factory=list)
    git_info: GitInfo = Field(default_factory=GitInfo)
    compliance_config: ComplianceConfig = Field(
        default_factory=ComplianceConfig.create_default, description="Compliance configuration for the deployment"
    )
    # Overriding metadata to store tags/labels/annotations as needed
    # But can remain CommonMetadataFields for uniformity.
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)
    deployment_date_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deployment_manager: Optional[object] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @validator("configuration")
    def validate_configuration(cls, v: Dict[str, object]) -> Dict[str, object]:
        """Validate that all configuration values are dictionaries."""
        if not all(isinstance(config, dict) for config in v.values()):
            raise ValueError("All configurations must be dictionaries")
        return v


class ModuleRegistry(BaseConfigModel):
    """
    Module registration information.
    Adds a required 'name' field.
    """

    name: str


class ModuleBase(BaseConfigModel):
    """
    Base class for all modules.
    Represents a deployable unit of infrastructure.
    Inherits from BaseConfigModel.
    Adds a required 'name' field.
    """

    name: str = Field(..., description="Module name")


# -----------------------
# Resource Model
# -----------------------
class ResourceModel(BaseModel):
    """
    Resource model representing infrastructure resources.

    Attributes:
        name: The resource's name.
        metadata: Common metadata fields (tags, labels, annotations).
        created_at: Resource creation timestamp.
        updated_at: Resource last update timestamp.
    """

    name: str = Field(..., description="Resource name")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# -----------------------
# Deployment Result and Interfaces
# -----------------------
class ModuleDeploymentResult(BaseModel):
    """
    Results from a module deployment operation.

    Attributes:
        config: List of ResourceModel configurations for sharing
        compliance: List of compliance/tracing info
        errors: List of error messages if any occurred
        metadata: Additional deployment metadata (tags, labels, annotations, etc.)
    """

    config: List[ResourceModel] = Field(default_factory=list)
    compliance: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)


class DeploymentContext(Protocol):
    """
    Protocol defining the deployment context interface.
    """

    def get_config(self) -> BaseConfigModel:
        """
        Retrieve the configuration for the deployment.

        Returns:
            BaseConfigModel: The configuration model for this deployment context.
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
    Minimalistic: just validate config and deploy, plus dependencies listing.
    """

    def validate(self, config: BaseConfigModel) -> List[str]:
        """
        Validate module configuration and return a list of errors if any.

        Args:
            config (BaseConfigModel): The configuration to validate.

        Returns:
            List[str]: Validation error messages, empty if valid.
        """
        ...

    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult:
        """
        Deploy the module using the provided deployment context.

        Args:
            ctx (DeploymentContext): The deployment context.

        Returns:
            ModuleDeploymentResult: Deployment results.
        """
        ...

    def dependencies(self) -> List[str]:
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
    Provides a centralized store for cross-module metadata.

    Attributes:
        global_tags: Global tags
        global_labels: Global labels
        global_annotations: Global annotations
        git_metadata: Git metadata
        modules_metadata: Module-specific metadata
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
    metadata: CommonMetadataFields


# -----------------------
# Setup Global Metadata
# -----------------------
def setup_global_metadata(init_config: InitConfig) -> None:
    """
    Initialize global metadata for resources using the provided InitConfig.
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

        # Merge global tags
        base_tags = {**base_metadata, **init_config.metadata.tags}
        # Merge global labels and add git_labels
        base_labels = {**base_metadata, **init_config.metadata.labels, **git_labels}
        # Merge global annotations
        base_annotations = {**base_metadata, **init_config.metadata.annotations}

        metadata.set_tags({k: str(v) for k, v in base_tags.items()})
        metadata.set_labels({k: str(v) for k, v in base_labels.items()})
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
    Configuration Management class for retrieving and caching Pulumi configuration.
    """

    def __init__(self) -> None:
        self.pulumi_config = pulumi.Config()
        self._config_cache: Optional[Dict[str, object]] = None
        self._module_configs: Dict[str, Dict[str, object]] = {}

    def get_config(self) -> Dict[str, object]:
        """Retrieve full configuration from Pulumi stack config, caching results."""
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
        """Get configuration for a specific module from cached config."""
        if module_name in self._module_configs:
            return self._module_configs[module_name]
        config = self.get_config()
        module_config = cast(Dict[str, object], config.get(module_name, {}))
        self._module_configs[module_name] = module_config
        log.debug(f"Module {module_name} config: {module_config}")
        return module_config

    def get_enabled_modules(self) -> List[str]:
        """Return a list of enabled modules from the cached configuration."""
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
    Global metadata structure for top-level stack outputs.
    """

    tags: Dict[str, str] = Field(default_factory=dict, description="Global public cloud resource tags")
    labels: Dict[str, str] = Field(default_factory=dict, description="Global Kubernetes labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Global Kubernetes annotations")


class SourceRepository(BaseModel):
    """
    Source repository information.
    """

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
    secrets: Optional[Dict[str, object]] = Field(default=None, description="Sensitive info like credentials/tokens")


class ModuleDefaults(BaseModel):
    """
    Default configuration for modules.
    """

    enabled: bool = Field(default=False, description="Whether the module is enabled")
    config: Dict[str, object] = Field(default_factory=dict, description="Module-specific configuration")


__all__ = [
    "CoreError",
    "ModuleLoadError",
    "CommonMetadataFields",
    "GitInfo",
    "OwnershipInfo",
    "AtoConfig",
    "ProjectOwnership",
    "StackConfig",
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
    "setup_global_metadata",
    "ConfigManager",
    "GlobalMetadata",
    "SourceRepository",
    "StackConfig",
    "StackOutputs",
    "ModuleDefaults",
]
