# ./modules/core/types/__init__.py
"""
Core module types implementation (revision10).

This revision removes all TypedDict usage and uses Pydantic models exclusively.
This enhances runtime validation, consistency, and the ability to leverage Pydantic's
advanced features (validation, defaults, and type conversion) throughout the codebase.

Changes from previous revision:
- Converted OwnershipInfo, AtoConfig, ProjectOwnership from TypedDict to Pydantic models
- Ensured compliance and project config classes now consistently use Pydantic models.
- Maintained DRY principles, strict typing, and compliance/security considerations.

Conventions and Requirements:
- Strict typing with Pyright in strict mode.
- No use of Any or typed dicts; replaced with Pydantic models.
- Pydantic models for validation and runtime checks.
- Clear docstrings and alignment with Pulumi IaC best practices.
- No broad `except Exception` unless re-raised after logging.
- Security, compliance, and maintainability integrated.
- No hardcoded credentials or secrets.
- Follow PEP 8, PEP 257, and all style/documentation standards.

This remains a large omnibus module for testing before splitting into submodules.
"""

from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Dict, List, Optional, Union, Protocol, ClassVar, cast, Any
from pydantic import BaseModel, Field, validator, ConfigDict
import pulumi
from pulumi import Resource, log


# -----------------------
# Exceptions
# -----------------------
class CoreError(Exception):
    """Base exception for core module errors."""

    pass


class ModuleLoadError(CoreError):
    """Exception raised when a module cannot be loaded."""

    pass


class ModuleDeploymentError(CoreError):
    """Exception raised when a module deployment fails."""

    pass


# -----------------------
# Common Metadata Fields
# -----------------------
class CommonMetadataFields(BaseModel):
    """
    Common metadata fields used across multiple classes for tagging,
    labeling, and annotating resources.

    Attributes:
        tags: Key-value tags for resources.
        labels: Key-value labels for resources.
        annotations: Key-value annotations for resources.
    """

    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value tags for resources."
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value labels for resources."
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value annotations for resources."
    )


# -----------------------
# Git Metadata
# -----------------------
class GitInfo(BaseModel):
    """
    Git Repository Metadata.

    Attributes:
        commit_hash: Current git commit hash or "unk" if unknown.
        branch_name: Current git branch name or "unk" if unknown.
        remote_url: Current git remote URL or "unk" if unknown.
        release_tag: Optional release tag if the current commit has a semver tag.
    """

    commit_hash: str = Field(
        default="unk",
        description="Current git commit hash"
    )
    branch_name: str = Field(default="unk", description="Current git branch name")
    remote_url: str = Field(default="unk", description="Current git remote URL")
    release_tag: Optional[str] = Field(
        default=None, description="Git release tag if applicable."
    )

    def model_dump(self) -> Dict[str, str]:
        """Return a dict with commit, branch, remote, and optional tag fields."""
        data = {
            "commit": self.commit_hash,
            "branch": self.branch_name,
            "remote": self.remote_url,
        }
        if self.release_tag:
            data["tag"] = self.release_tag
        return data


# -----------------------
# Compliance and Project Configuration
# -----------------------
class OwnershipInfo(BaseModel):
    """
    Owner contact information.

    Attributes:
        name: Name of the owner or owning team.
        contacts: List of contact methods (emails, slack channels, etc.).
    """

    name: str
    contacts: List[str] = Field(default_factory=list)


class AtoConfig(BaseModel):
    """
    Authority to Operate (ATO) configuration for production deployments.

    Attributes:
        id: ATO identifier.
        authorized: ISO datetime the project was authorized to operate.
        eol: ISO datetime marking end-of-life.
        last_touch: ISO datetime of the last compliance touch.
    """

    id: str
    authorized: str
    eol: str
    last_touch: str


class ProjectOwnership(BaseModel):
    """
    Project ownership structure, including owner and operations contacts.

    Attributes:
        owner: OwnershipInfo for the project's owner.
        operations: OwnershipInfo for operations team contacts.
    """

    owner: OwnershipInfo
    operations: OwnershipInfo


class ScipConfig(BaseModel):
    """
    SCIP (project) configuration for compliance.

    Attributes:
        environment: Environment name, e.g. 'prod-us-west'
        production: Boolean indicating if this is a production environment.
        ownership: ProjectOwnership model with owner and operations info.
        ato: AtoConfig with authorization details.
    """

    environment: str = Field(
        ...,
        description="Environment name, e.g. 'prod-us-west'"
    )
    production: bool = Field(
        default=False,
        description="Whether environment is production."
    )
    ownership: ProjectOwnership
    ato: AtoConfig


class FismaConfig(BaseModel):
    """
    FISMA compliance configuration.

    Attributes:
        level: FISMA compliance level ('low', 'moderate', 'high').
        mode: Enforcement mode ('disabled', 'warn', or 'enforcing').
    """

    level: str = Field(default="moderate", description="FISMA compliance level.")
    mode: str = Field(default="warn", description="FISMA compliance mode.")


class NistConfig(BaseModel):
    """
    NIST compliance configuration.

    Attributes:
        auxiliary: Enabled auxiliary NIST controls.
        exceptions: Disabled NIST exception controls.
    """

    auxiliary: List[str] = Field(
        default_factory=list,
        description="Enabled auxiliary NIST controls."
    )
    exceptions: List[str] = Field(
        default_factory=list,
        description="Disabled NIST exception controls."
    )


class ComplianceConfig(BaseModel):
    """
    Consolidated compliance configuration mapping to 'compliance' in stack config.

    Includes:
    - project: ScipConfig with environment and ATO details.
    - fisma: FismaConfig for FISMA compliance.
    - nist: NistConfig for NIST compliance.
    """

    project: ScipConfig
    fisma: FismaConfig
    nist: NistConfig

    @classmethod
    def from_pulumi_config(
        cls,
        config: pulumi.Config,
        timestamp: datetime
    ) -> "ComplianceConfig":
        """
        Create ComplianceConfig from Pulumi stack config.
        If environment is production, 'authorized' and 'eol' must be present.
        """
        try:
            raw = config.get_object("compliance") or {}
            compliance_data = cast(Dict[str, object], raw)

            project_data = cast(Dict[str, object], compliance_data.get("project", {}))
            is_production = bool(project_data.get("production", False))

            ato_data = cast(Dict[str, object], project_data.get("ato", {}))
            current_time = timestamp.isoformat()

            if is_production and "authorized" not in ato_data:
                raise ValueError("Production environments require authorization date.")

            authorized_date = str(
                ato_data.get("authorized", current_time)
            )
            eol_date = str(
                ato_data.get("eol", (timestamp + timedelta(hours=24)).isoformat())
            )

            # If project not defined, provide defaults
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
        Create a default compliance configuration for a non-production dev environment.
        """
        timestamp = datetime.now(timezone.utc)
        current_time = timestamp.isoformat()

        return cls(
            project=ScipConfig(
                environment="dev",
                production=False,
                ownership=ProjectOwnership(
                    owner=OwnershipInfo(name="default", contacts=[]),
                    operations=OwnershipInfo(name="default", contacts=[]),
                ),
                ato=AtoConfig(
                    id="default",
                    authorized=current_time,
                    eol=(timestamp + timedelta(hours=24)).isoformat(),
                    last_touch=current_time,
                ),
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
    - enabled: Whether the module or config is active.
    - parent: Optional parent identifier.
    - dependencies: List of dependencies.
    - configuration: Arbitrary configuration dictionary.
    - metadata: CommonMetadataFields for tags, labels, annotations.
    """

    enabled: bool = Field(default=False)
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    configuration: Dict[str, object] = Field(default_factory=dict)
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)


class InitializationConfig(BaseConfigModel):
    """
    Configuration for core module initialization.

    Adds:
    - pulumi_config: Pulumi configuration object or dict
    - stack_name, project_name: Identifiers
    - global_depends_on: Global resource dependencies
    - git_info: Git repository metadata
    - compliance_config: Compliance configuration
    - metadata: CommonMetadataFields
    - deployment_date_time: Timestamp of deployment
    - deployment_manager: Optional deployment manager object
    """

    pulumi_config: Union[pulumi.Config, Dict[str, object]]
    stack_name: str
    project_name: str
    global_depends_on: List[Resource] = Field(default_factory=list)
    git_info: GitInfo = Field(default_factory=GitInfo)
    compliance_config: ComplianceConfig = Field(
        default_factory=ComplianceConfig.create_default,
        description="Compliance configuration for the deployment"
    )
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)
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


class ModuleRegistry(BaseConfigModel):
    """
    Module registration information.
    Requires a 'name' field.
    """

    name: str


class ModuleBase(BaseConfigModel):
    """
    Base class for all modules.
    Adds a required 'name' field, representing a deployable unit of infrastructure.
    """

    name: str = Field(..., description="Module name")


# -----------------------
# Resource Model
# -----------------------
class ResourceModel(BaseModel):
    """
    Resource model representing infrastructure resources.

    Attributes:
        name: Resource name
        metadata: Common metadata fields
        created_at: Timestamp of resource creation
        updated_at: Timestamp of last update
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
        config: List of ResourceModel configurations
        compliance: List of compliance/tracing info
        errors: List of errors encountered
        metadata: Additional deployment metadata
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
            BaseConfigModel: The configuration model.
        """
        ...

    def deploy(self) -> ModuleDeploymentResult:
        """
        Execute the deployment and return results.

        Returns:
            ModuleDeploymentResult: Deployment result data.
        """
        ...


class ModuleInterface(Protocol):
    """
    Module interface defining lifecycle and validation methods.

    Methods:
        validate(config): Validate module configuration
        deploy(ctx): Deploy the module using a given context
        dependencies(): Return a list of dependent modules
    """

    def validate(self, config: BaseConfigModel) -> List[str]:
        """Validate module configuration and return errors if any."""
        ...

    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult:
        """Deploy the module using the provided context."""
        ...

    def dependencies(self) -> List[str]:
        """Return a list of module dependencies."""
        ...


# -----------------------
# Metadata Singleton
# -----------------------
class MetadataSingleton:
    """
    Global metadata thread-safe singleton.

    Stores global tags, labels, annotations, git metadata, and module-specific metadata.
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

    def set_module_metadata(
        self,
        module_name: str,
        metadata: Dict[str, object]
    ) -> None:
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

    Attributes:
        project_name: Name of the project
        stack_name: Name of the stack
        git_info: GitInfo model with repository metadata
        metadata: CommonMetadataFields for tags, labels, annotations
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
            "git.commit": git_info.get("commit", "unk"),
            "git.branch": git_info.get("branch", "unk"),
            "git.repository": git_info.get("remote", "unk"),
        }

        base_metadata = {
            "managed-by": f"pulumi-{init_config.project_name}-{init_config.stack_name}",
            "project": init_config.project_name,
            "stack": init_config.stack_name,
            "git": git_info,
        }

        base_tags = {**base_metadata, **init_config.metadata.tags}
        base_labels = {**base_metadata, **init_config.metadata.labels, **git_labels}
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
# Global Metadata and Stack Config
# -----------------------
class GlobalMetadata(BaseModel):
    """
    Global metadata structure for top-level stack outputs.
    """

    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Global public cloud resource tags"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Global Kubernetes labels"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Global Kubernetes annotations"
    )


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
    Holds compliance, metadata, and source repository info.
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
        description="Sensitive credentials or tokens"
    )


class ModuleDefaults(BaseModel):
    """
    Default configuration for modules.
    """

    enabled: bool = Field(default=False, description="Whether the module is enabled")
    config: Dict[str, object] = Field(
        default_factory=dict,
        description="Module-specific configuration"
    )


__all__ = [
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
    "setup_global_metadata",
    "GlobalMetadata",
    "SourceRepository",
    "StackConfig",
    "StackOutputs",
    "ModuleDefaults",
]
