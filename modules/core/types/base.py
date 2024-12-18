# ./modules/core/types/base.py
"""
Core module base types implementation.

This module provides foundational types and interfaces for the core module.
It includes data structures for Git metadata, compliance configurations,
initialization settings, and module management. These types are essential
for ensuring consistent configuration and deployment across the platform.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any, Protocol, ClassVar
from pydantic import BaseModel, Field, ConfigDict, validator
from threading import Lock

import pulumi
from pulumi import Resource, log

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

from datetime import datetime
from typing import Dict, Any, List, Protocol, Optional
from pydantic import BaseModel, Field

from .base import ResourceBase, ConfigBase, DeploymentContext


class ModuleDeploymentResult(BaseModel):
    """
    Module deployment outputs.

    Attributes:
        config (List[ResourceBase]): Configurations returned for use by other modules and stacks.
        compliance (List[str]): Compliance and traceability reporting metadata.
        resources (Dict[str, Any]): Resources created by the module for users to interact with.
    """

    config: List[ResourceBase]
    compliance: List[str]
    resources: Dict[str, Any]


class DeploymentContext(Protocol):
    """Deployment context interface."""

    def get_config(self) -> ConfigBase: ...
    def deploy(self) -> ModuleDeploymentResult: ...


class ModuleInterface(Protocol):
    """Base interface for all modules."""

    def validate_config(self, config: ConfigBase) -> List[str]: ...
    def validate_resources(self, resources: List[ResourceBase]) -> List[str]: ...
    def deploy(self, config: ConfigBase) -> ModuleDeploymentResult: ...


class ResourceManagerInterface(Protocol):
    """Interface for resource managers."""

    def get_or_create(self) -> tuple[ResourceBase, Dict[str, Any]]: ...
    def deploy_resources(self) -> Dict[str, ResourceBase]: ...


class ResourceMetadata(BaseModel):
    """Common resource metadata."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)


class ModuleDeploymentResult(BaseModel):
    """
    Results from a module deployment operation.

    Attributes:
        success: Whether the deployment was successful
        version: Version of the deployed module
        resources: List of created resource names/IDs
        errors: List of error messages if any occurred
        metadata: Additional deployment metadata
    """

    success: bool
    version: Optional[str] = Field(default="")
    resources: List[str] = Field(default_factory=list, description="List of resource names/identifiers")
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class DeploymentContext(Protocol):
    """Protocol defining the deployment context interface."""

    def get_config(self) -> Dict[str, Any]: ...
    def deploy(self) -> ModuleDeploymentResult: ...


class ModuleInterface(Protocol):
    """Enhanced module interface with validation."""

    def validate_config(self, config: Dict[str, Any]) -> List[str]: ...
    def pre_deploy_check(self) -> List[str]: ...
    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult: ...
    def post_deploy_validation(self, result: ModuleDeploymentResult) -> List[str]: ...
    def get_dependencies(self) -> List[str]: ...


class ResourceManagerInterface(Protocol):
    """Protocol for resource managers."""

    def get_or_create(self) -> tuple[Any, Dict[str, Any]]: ...
    def deploy_resources(self) -> Dict[str, Any]: ...


class CloudProvider(Protocol):
    """Provider-agnostic interface for cloud providers."""

    def get_provider(self) -> Any: ...
    def get_region(self) -> str: ...
    def get_metadata(self) -> Dict[str, Any]: ...

class CoreError(Exception):
    """Base exception for core module."""

    pass


class ModuleLoadError(CoreError):
    """Exception raised when a module cannot be loaded."""


class MetadataSingleton:
    """
    Global metadata thread-safe singleton class.
    Provides a centralized store for all cross module metadata.
    Each module is allowed full autonomy over its own metadata namespace.
    Modules can publish and retrieve metadata to and from the global singleton.
    Modules can also read metadata from any other module's namespace in the global singleton if needed.
    """

    _instance: Optional["MetadataSingleton"] = None
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls) -> "MetadataSingleton":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        """Initialize metadata storage."""
        if not hasattr(self, "_initialized"):
            self._global_tags: Dict[str, str] = {}
            self._global_labels: Dict[str, str] = {}
            self._global_annotations: Dict[str, str] = {}
            self._git_metadata: Dict[str, Any] = {}
            self._modules_metadata: Dict[str, Dict[str, Any]] = {}
            self._initialized = True

    @property
    def global_tags(self) -> Dict[str, str]:
        """Get global tags."""
        with self._lock:
            return self._global_tags.copy()

    @property
    def global_labels(self) -> Dict[str, str]:
        """Get global labels."""
        with self._lock:
            return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        """Get global annotations."""
        with self._lock:
            return self._global_annotations.copy()

    @property
    def git_metadata(self) -> Dict[str, Any]:
        """Get Git metadata."""
        with self._lock:
            return self._git_metadata.copy()

    @property
    def modules_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all modules metadata."""
        with self._lock:
            return self._modules_metadata.copy()

    def set_tags(self, tags: Dict[str, str]) -> None:
        """Set global tags."""
        with self._lock:
            self._global_tags.update(tags)

    def set_labels(self, labels: Dict[str, str]) -> None:
        """Set global labels."""
        with self._lock:
            self._global_labels.update(labels)

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        """Set global annotations."""
        with self._lock:
            self._global_annotations.update(annotations)

    def set_git_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set Git metadata."""
        with self._lock:
            self._git_metadata.update(metadata)

    def set_module_metadata(self, module_name: str, metadata: Dict[str, Any]) -> None:
        """
        Set metadata for a specific module.
        Each module's metadata is stored under its own namespace.
        """
        with self._lock:
            if module_name not in self._modules_metadata:
                self._modules_metadata[module_name] = {}
            self._modules_metadata[module_name].update(metadata)

    def get_module_metadata(self, module_name: str) -> Dict[str, Any]:
        """Get metadata for a specific module."""
        with self._lock:
            return self._modules_metadata.get(module_name, {}).copy()


class InitConfig(Protocol):
    project_name: str
    stack_name: str
    git_info: Any
    metadata: Dict[str, Dict[str, str]]


def setup_global_metadata(init_config: InitConfig) -> None:
    """Initialize global metadata for resources."""
    try:
        metadata = MetadataSingleton()

        # Create git metadata labels
        git_info = init_config.git_info.model_dump()
        git_labels = {
            "git.commit": git_info["commit_hash"],
            "git.branch": git_info["branch_name"],
            "git.repository": git_info["remote_url"],
        }

        # Create base metadata to feed into tags, labels, and annotations
        base_metadata = {
            "managed-by": f"pulumi-{init_config.project_name}-{init_config.stack_name}",
            "project": init_config.project_name,
            "stack": init_config.stack_name,
            "git": init_config.git_info.model_dump(),
        }

        # Create base tags by merging base metadata and init config tags
        base_tags = {
            **base_metadata,
            **init_config.metadata.get("tags", {}),
        }

        # Create base labels by merging base metadata and init config labels
        base_labels = {
            **base_metadata,
            **init_config.metadata.get("labels", {}),
        }

        # Create base annotations by merging base metadata and init config annotations
        base_annotations = {
            **base_metadata,
            **init_config.metadata.get("annotations", {}),
        }

        # Merge all labels
        all_labels = {
            **base_labels,
            **git_labels,
            **(init_config.metadata.get("labels", {})),
        }

        # Set global metadata
        metadata.set_tags(base_tags)
        metadata.set_labels(all_labels)
        metadata.set_annotations(base_annotations)
        metadata.set_git_metadata(git_info)

        log.info("Global metadata initialized successfully")

    except Exception as e:
        log.error(f"Failed to setup global metadata: {str(e)}")
        raise


class ConfigManager:
    """Configuration Management Class"""

    def __init__(self):
        """Initialize ConfigManager with Pulumi config"""
        self.pulumi_config = pulumi.Config()
        self._config_cache = None
        self._module_configs = {}

    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration."""
        if self._config_cache is None:
            # Load raw config from Pulumi
            raw_config = {}
            for module_name in ["aws", "kubernetes"]:
                try:
                    module_config = pulumi.Config(module_name).get_object("") or {}
                    raw_config[module_name] = module_config
                except Exception as e:
                    log.debug(f"No config found for module {module_name}: {str(e)}")

            self._config_cache = raw_config
            log.debug(f"Loaded config: {raw_config}")

        return self._config_cache

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        if module_name in self._module_configs:
            return self._module_configs[module_name]

        config = self.get_config()
        module_config = config.get(module_name, {})

        # Cache the config
        self._module_configs[module_name] = module_config
        log.debug(f"Module {module_name} config: {module_config}")
        return module_config

    def get_enabled_modules(self) -> List[str]:
        """Get list of enabled modules."""
        enabled_modules = []
        config = self.get_config()

        # Load enabled modules from config
        # TODO: Replace hardcoded list with a dynamic module loader
        for module_name in ["aws", "kubernetes"]:
            module_config = config.get(module_name, {})
            if module_config.get("enabled", False):
                enabled_modules.append(module_name)
                log.info(f"Module {module_name} is enabled")

        log.info(f"Enabled modules: {enabled_modules}")
        return enabled_modules

from typing import List, Dict, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
import pulumi
from pulumi import log


class OwnershipInfo(TypedDict):
    """Owner contact information."""
    name: str
    contacts: List[str]


class AtoConfig(TypedDict):
    """ATO (Authority to Operate) configuration."""
    id: str
    authorized: str  # ISO datetime
    eol: str        # ISO datetime
    last_touch: str # ISO datetime


class ProjectOwnership(TypedDict):
    """Project ownership structure."""
    owner: OwnershipInfo
    operations: OwnershipInfo


class ProjectProviders(TypedDict):
    """Cloud provider configuration."""
    name: List[str]
    regions: List[str]


class ScipConfig(BaseModel):
    """SCIP project configuration."""
    environment: str = Field(..., description="e.g., prod-us-west")
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

    Maps to the 'compliance' section of stack outputs.
    """
    project: ScipConfig
    fisma: FismaConfig
    nist: NistConfig

    @classmethod
    def from_pulumi_config(cls, config: pulumi.Config, timestamp: datetime) -> "ComplianceConfig":
        """
        Create ComplianceConfig from Pulumi config.

        Args:
            config: Pulumi configuration object
            timestamp: Current timestamp for configuration creation

        Returns:
            ComplianceConfig: Configuration instance
        """
        try:
            # Get compliance config from Pulumi config
            compliance_data = config.get_object("compliance") or {}

            # Get project config or initialize default
            project_data = compliance_data.get("project", {})

            # Determine if this is a production deployment
            is_production = project_data.get("production", False)

            # Handle ATO dates
            ato_data = project_data.get("ato", {})
            current_time = timestamp.isoformat()

            if is_production:
                # Production environments must have authorized date in config
                if "authorized" not in ato_data:
                    raise ValueError("Production environments require 'authorized' date in ATO configuration")
                authorized_date = ato_data["authorized"]
            else:
                # Non-production uses current timestamp
                authorized_date = current_time

            # Set EOL date
            if "eol" in ato_data:
                # Use configured EOL if provided
                eol_date = ato_data["eol"]
            else:
                if is_production:
                    # Production should have explicit EOL
                    raise ValueError("Production environments require 'eol' date in ATO configuration")
                else:
                    # Dev/non-prod gets 24h EOL from last_touch
                    eol_date = (timestamp + timedelta(hours=24)).isoformat()

            # Ensure required nested structures exist
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
                # Update ATO dates in existing project data
                compliance_data["project"]["ato"] = {
                    "id": ato_data.get("id", "dev"),
                    "authorized": authorized_date,
                    "eol": eol_date,
                    "last_touch": current_time
                }

            if "fisma" not in compliance_data:
                compliance_data["fisma"] = {"level": "moderate", "mode": "warn"}

            if "nist" not in compliance_data:
                compliance_data["nist"] = {"auxiliary": [], "exceptions": []}

            return cls(**compliance_data)

        except Exception as e:
            log.error(f"Failed to load compliance config: {str(e)}")
            # Return default config
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
            project=ScipConfig(
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

    def model_dump(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "project": self.project.model_dump(),
            "fisma": self.fisma.model_dump(),
            "nist": self.nist.model_dump()
        }


from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .metadata import StackConfig


class StackOutputs(BaseModel):
    """
    Complete stack outputs structure.

    Maps to the complete stack outputs JSON structure.
    """
    stack: StackConfig
    secrets: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sensitive information like credentials or tokens"
    )


class ModuleDefaults(BaseModel):
    """
    Default configuration for modules.

    Provides standard configuration defaults that can be overridden
    by specific module implementations.
    """
    enabled: bool = Field(
        default=False,
        description="Whether the module is enabled"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Module-specific configuration"
    )


class ConfigurationValidator(BaseModel):
    """Configuration validation interface."""
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        raise NotImplementedError

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .base import ResourceBase
from .compliance import ComplianceConfig


class GlobalMetadata(BaseModel):
    """
    Global metadata structure.

    Maps to the 'metadata' section of stack outputs.
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
    """Source repository information."""
    branch: str
    commit: str
    remote: str
    tag: Optional[str] = None


class StackConfig(BaseModel):
    """
    Root stack configuration.

    Maps to the root level of stack outputs.
    """
    compliance: ComplianceConfig
    metadata: GlobalMetadata
    source_repository: SourceRepository
    k8s_component_versions: Dict[str, Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Versions of Kubernetes components"
    )


class ResourceMetadata(ResourceBase):
    """
    Resource metadata structure.

    Attributes:
        tags (Dict[str, str]): Resource tags
        labels (Dict[str, str]): Resource labels
        annotations (Dict[str, str]): Resource annotations
        created_at (datetime): Resource creation timestamp
        updated_at (datetime): Resource last update timestamp
    """
    tags: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
