# pulumi/core/types.py

"""
Types and Data Structures Module

This module defines all shared data classes and types used across all modules.
It provides type-safe configuration structures using Pydantic models and TypedDict.
"""

from typing import Dict, List, Optional, Any, TypedDict, Protocol
from pydantic import BaseModel, Field, validator
from datetime import datetime
import pulumi
import pulumi_kubernetes as k8s


class NamespaceConfig(BaseModel):
    """
    Configuration for Kubernetes namespace creation.

    Attributes:
        name: Name of the namespace
        labels: Kubernetes labels to apply
        annotations: Kubernetes annotations to apply
        finalizers: List of finalizer strings
        protect: Whether to protect the resource from deletion
        retain_on_delete: Whether to retain the resource on stack deletion
        ignore_changes: List of fields to ignore during updates
        custom_timeouts: Custom timeout values for operations
    """
    name: str
    labels: Dict[str, str] = Field(default_factory=lambda: {"ccio.v1/app": "kargo"})
    annotations: Dict[str, str] = Field(default_factory=dict)
    finalizers: List[str] = Field(default_factory=lambda: ["kubernetes"])
    protect: bool = False
    retain_on_delete: bool = False
    ignore_changes: List[str] = Field(
        default_factory=lambda: ["metadata", "spec"]
    )
    custom_timeouts: Dict[str, str] = Field(
        default_factory=lambda: {
            "create": "5m",
            "update": "10m",
            "delete": "10m"
        }
    )


class FismaConfig(BaseModel):
    """
    FISMA compliance configuration.

    Attributes:
        enabled: Whether FISMA compliance is enabled
        level: FISMA impact level
        ato: Authority to Operate details
    """
    enabled: bool = False
    level: Optional[str] = None
    ato: Dict[str, str] = Field(default_factory=dict)

    @validator("enabled", pre=True)
    def parse_enabled(cls, v: Any) -> bool:
        """Convert various input types to boolean."""
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class NistConfig(BaseModel):
    """
    NIST compliance configuration.

    Attributes:
        enabled: Whether NIST controls are enabled
        controls: List of NIST control identifiers
        auxiliary: Additional NIST controls
        exceptions: NIST control exceptions
    """
    enabled: bool = False
    controls: List[str] = Field(default_factory=list)
    auxiliary: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)

    @validator("enabled", pre=True)
    def parse_enabled(cls, v: Any) -> bool:
        """Convert various input types to boolean."""
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class ScipConfig(BaseModel):
    """
    SCIP-specific configuration.

    Attributes:
        environment: Target environment identifier
        ownership: Resource ownership metadata
        provider: Provider-specific configuration
    """
    environment: Optional[str] = None
    ownership: Dict[str, Any] = Field(default_factory=dict)
    provider: Dict[str, Any] = Field(default_factory=dict)


class ComplianceConfig(BaseModel):
    """
    Comprehensive compliance configuration.

    Attributes:
        fisma: FISMA compliance settings
        nist: NIST compliance settings
        scip: SCIP-specific settings
    """
    fisma: FismaConfig = Field(default_factory=FismaConfig)
    nist: NistConfig = Field(default_factory=NistConfig)
    scip: ScipConfig = Field(default_factory=ScipConfig)

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "ComplianceConfig":
        """
        Merge user configuration with default configuration.

        Args:
            user_config: User-provided configuration dictionary

        Returns:
            ComplianceConfig: Merged configuration object
        """
        fisma_config = FismaConfig(**(user_config.get("fisma", {}) or {}))
        nist_config = NistConfig(**(user_config.get("nist", {}) or {}))
        scip_config = ScipConfig(**(user_config.get("scip", {}) or {}))

        return cls(
            fisma=fisma_config,
            nist=nist_config,
            scip=scip_config
        )

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.

        Returns:
            Dict[str, Any]: Configuration as a dictionary
        """
        base_dict = super().dict(*args, **kwargs)

        # Ensure nested models are also converted to dictionaries
        base_dict["fisma"] = self.fisma.dict()
        base_dict["nist"] = self.nist.dict()
        base_dict["scip"] = self.scip.dict()

        return base_dict


class ResourceMetadata(BaseModel):
    """
    Common resource metadata.

    Attributes:
        created_at: Resource creation timestamp
        updated_at: Last update timestamp
        labels: Resource labels
        annotations: Resource annotations
    """
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

    @validator("updated_at", pre=True, always=True)
    def update_timestamp(cls, v: Any, values: Dict[str, Any]) -> datetime:
        """Ensure updated_at is always current."""
        return datetime.utcnow()


class ModuleBase(BaseModel):
    """
    Base class for all module configurations.

    Attributes:
        enabled: Whether the module is enabled
        version: Module version
        metadata: Resource metadata
    """
    enabled: bool = False
    version: Optional[str] = None
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


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


class InitializationConfig(BaseModel):
    """
    Configuration for core module initialization.

    This class encapsulates all necessary configuration and state needed
    for initializing and managing the core module components.

    Attributes:
        config: Pulumi configuration object
        stack_name: Name of the current Pulumi stack
        project_name: Name of the Pulumi project
        default_versions: Default versions for all modules
        versions: Current versions of deployed modules
        configurations: Module-specific configurations
        global_depends_on: Global resource dependencies
        k8s_provider: Kubernetes provider instance
        git_info: Git repository information
        compliance_config: Compliance configuration
        metadata: Resource metadata
    """
    config: Any  # Pulumi.Config can't be type-hinted directly
    stack_name: str
    project_name: str
    default_versions: Dict[str, Any]
    versions: Dict[str, str] = Field(default_factory=dict)
    configurations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    global_depends_on: List[Any] = Field(default_factory=list)  # Pulumi.Resource list
    k8s_provider: Optional[Any] = None  # k8s.Provider
    git_info: Dict[str, str] = Field(default_factory=dict)
    compliance_config: ComplianceConfig = Field(default_factory=ComplianceConfig)
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)

    @validator("config")
    def validate_pulumi_config(cls, v: Any) -> Any:
        """Validate that config is a Pulumi.Config instance."""
        if not isinstance(v, pulumi.Config):
            raise ValueError("config must be an instance of pulumi.Config")
        return v

    @validator("k8s_provider")
    def validate_k8s_provider(cls, v: Any) -> Any:
        """Validate that k8s_provider is a k8s.Provider instance if provided."""
        if v is not None and not isinstance(v, k8s.Provider):
            raise ValueError("k8s_provider must be an instance of k8s.Provider")
        return v

    def update_versions(self, module_name: str, version: str) -> None:
        """Update version information for a module."""
        self.versions[module_name] = version

    def add_dependency(self, resource: Any) -> None:
        """Add a resource to global dependencies."""
        if resource not in self.global_depends_on:
            self.global_depends_on.append(resource)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        return self.configurations.get(module_name, {})

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            pulumi.Config: lambda v: str(v),
            k8s.Provider: lambda v: str(v)
        }


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


class ModuleDeploymentResult(BaseModel):
    """
    Results from a module deployment operation.

    Attributes:
        success: Whether the deployment was successful
        version: Deployed module version
        resources: List of created resource IDs
        errors: Any errors that occurred
        metadata: Additional deployment metadata
    """
    success: bool
    version: str
    resources: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata information."""
        self.metadata[key] = value


class ModuleRegistry(BaseModel):
    """Registry for available modules and their configurations."""
    modules: Dict[str, ModuleBase]
    providers: Dict[str, Any]
    dependencies: Dict[str, List[str]]

    def register_module(self, name: str, module: ModuleBase) -> None:
        """Register a module with the registry."""
        self.modules[name] = module

    def get_module(self, name: str) -> Optional[ModuleBase]:
        """Get a module by name."""
        return self.modules.get(name)

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

class DependencyResolver:
    """Resolves module deployment order based on dependencies."""

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry

    def resolve_deployment_order(
        self,
        modules: List[str]
    ) -> List[str]:
        """
        Returns modules in correct deployment order.
        Raises CircularDependencyError if circular dependency detected.
        """
        # TODO: Implementation using topological sort
        pass

class ModuleInterface(Protocol):
    """Protocol defining required module interface."""

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate module configuration."""
        ...

    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult:
        """Deploy module resources."""
        ...

    def get_dependencies(self) -> List[str]:
        """Get module dependencies."""
        ...

class AWSDeployer:
    def deploy(
        self,
        dependencies: Optional[List[pulumi.Resource]],
        managers: AWSManagers
    ) -> Tuple[str, pulumi.Resource, Dict[str, Any]]:
        """
        Deploys AWS infrastructure using provided managers.

        Args:
            dependencies: Optional resource dependencies
            managers: Dictionary of AWS service managers

        Returns:
            Tuple containing:
            - Version string
            - Main infrastructure resource
            - Output dictionary
        """
        try:
            # Initialize core infrastructure
            org_resource, org_data = managers["organization"].get_or_create()

            # Get organization root ID
            root_id = managers["organization"].get_root_id(org_data)

            # Deploy security controls
            security_outputs = managers["security"].deploy_security_controls()

            # Deploy networking
            network_outputs = managers["networking"].deploy_network_infrastructure()

            # Deploy resources
            resource_outputs = managers["resources"].deploy_resources()

            # Combine outputs
            outputs = {
                **security_outputs,
                **network_outputs,
                **resource_outputs,
                "organization_id": org_resource.id,
                "organization_arn": org_resource.arn,
                "root_id": root_id
            }

            return "1.0.0", org_resource, outputs

        except Exception as e:
            log.error(f"Deployment failed: {str(e)}")
            raise
