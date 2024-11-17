# konductor/core/types.py
from typing import Dict, Any, Optional
from pydantic import BaseModel
import pulumi

class InitializationConfig(BaseModel):
    """
    Represents the initialization configuration for the deployment.
    """
    config: pulumi.Config
    stack_name: str
    project_name: str
    default_versions: Dict[str, str]
    git_info: Optional[Dict[str, Any]] = None
    global_labels: Optional[Dict[str, str]] = None
    # Add other fields as necessary

class ModuleDeploymentResult(BaseModel):
    """
    Represents the result of deploying a module.
    """
    success: bool
    version: Optional[str]
    resources: Optional[Any]
    errors: Optional[str]
    metadata: Optional[Dict[str, Any]]


# ./modules/core/types.py

"""
Types and Data Structures Module

This module defines all shared data classes and types used across all modules.
It provides type-safe configuration structures using Pydantic models and TypedDict.
"""

from typing import Dict, List, Optional, Any, TypedDict, Protocol, Type, Tuple, Iterable, TypeVar, Union
from pydantic import BaseModel, Field, validator, ValidationError, PrivateAttr
from datetime import datetime
import pulumi
import pulumi_kubernetes as k8s
from pulumi import ResourceOptions, Resource, Output, log
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

from .interfaces import (
    DeploymentContext,
    ModuleInterface,
    ModuleDeploymentResult,
    ResourceMetadata
)

from .aws import AWSManagers

from dataclasses import dataclass, field


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


class ModuleBase(Protocol):
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

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate module configuration.

        Args:
            config: Module configuration dictionary

        Returns:
            List of validation error messages
        """
        try:
            if hasattr(ModuleBase, 'Config'):
                ModuleBase.Config(**config)
            return []
        except ValidationError as e:
            return [str(error) for error in e.errors()]
        except Exception as e:
            return [str(e)]


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


T = TypeVar('T')
MetadataType = Union[Dict[str, Any], ObjectMetaArgs, Output[Dict[str, Any]]]
ResourceType = TypeVar('ResourceType', bound=Resource)

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
    pulumi_config: Any  # Pulumi.Config can't be type-hinted directly
    stack_name: str
    project_name: str
    default_versions: Dict[str, Any]
    versions: Dict[str, str] = Field(default_factory=dict)
    configurations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    global_depends_on: List[Resource] = Field(default_factory=list)
    kubernetes_provider: Optional[k8s.Provider] = None  # k8s.Provider
    git_info: Dict[str, str] = Field(default_factory=dict)
    compliance_config: ComplianceConfig = Field(default_factory=ComplianceConfig)
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)

    # Private attributes for non-serializable objects
    _pulumi_config: pulumi.Config = PrivateAttr()
    _k8s_provider: Optional[k8s.Provider] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._pulumi_config = data.get('pulumi_config')
        self._k8s_provider = data.get('k8s_provider')
        self._validate_providers()

    def _validate_providers(self) -> None:
        """Validates provider configurations."""
        if not isinstance(self._pulumi_config, pulumi.Config):
            raise ValueError("pulumi_config must be an instance of pulumi.Config")
        if self._k8s_provider is not None and not isinstance(self._k8s_provider, k8s.Provider):
            raise ValueError("k8s_provider must be an instance of k8s.Provider")

    @property
    def config(self) -> pulumi.Config:
        """Returns the Pulumi config instance."""
        return self._pulumi_config

    @property
    def k8s_provider(self) -> Optional[k8s.Provider]:
        """Returns the Kubernetes provider instance."""
        return self._k8s_provider

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
        return modules  # Temporary return until proper implementation

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
