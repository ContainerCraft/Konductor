# ./modules/kubernetes/components/crossplane/types.py
"""
Crossplane component types.

This module defines the configuration types for the Crossplane component,
integrating all existing functionality and features.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ...types import KubernetesSubmoduleConfig
from pulumi import log


class ProviderConfig(BaseModel):
    """
    Configuration for a Crossplane provider.

    Attributes:
        name (str): The name of the provider.
        version (str): The version of the provider.
        config (Dict[str, Any]): Additional configuration settings for the provider.
    """
    name: str
    version: str
    config: Dict[str, Any] = Field(default_factory=dict)


class CrossplaneConfig(KubernetesSubmoduleConfig):
    """
    Crossplane module configuration.

    This class extends KubernetesSubmoduleConfig to include specific settings
    for configuring the Crossplane module.

    Attributes:
        enabled (bool): Indicates if the Crossplane module is enabled.
        namespace (str): The Kubernetes namespace for Crossplane resources.
        version (str): The version of Crossplane to deploy.
        providers (List[str]): List of providers to use with Crossplane.
        aws_provider_version (str): Version of the AWS provider.
        kubernetes_provider_version (str): Version of the Kubernetes provider.
        aws_provider_config (Dict[str, Any]): Configuration for the AWS provider.
        enable_external_secret_stores (bool): Enable external secret stores.
        enable_composition_revisions (bool): Enable composition revisions.
        metrics_enabled (bool): Enable metrics collection.
        debug_mode (bool): Enable debug mode for Crossplane.
        resource_limits (Dict[str, str]): Resource limits for Crossplane.
        resource_requests (Dict[str, str]): Resource requests for Crossplane.
        provider_configs (Dict[str, Any]): Provider-specific configurations.
        compositions (Optional[List[Dict[str, Any]]]): List of compositions.
        composite_resources (Optional[List[Dict[str, Any]]]): List of composite resources.
    """

    enabled: bool = Field(default=False, description="Whether the Crossplane module is enabled")
    namespace: str = Field(default="crossplane-system", description="Namespace for Crossplane resources")
    version: str = Field(default="1.18.0", description="Version of Crossplane to deploy")
    providers: List[str] = Field(default_factory=lambda: ["provider-aws", "provider-kubernetes"], description="List of providers to use")
    aws_provider_version: str = Field(default="v0.43.1", description="Version of the AWS provider")
    kubernetes_provider_version: str = Field(default="v0.10.0", description="Version of the Kubernetes provider")
    aws_provider_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the AWS provider")
    enable_external_secret_stores: bool = Field(default=True, description="Enable external secret stores")
    enable_composition_revisions: bool = Field(default=True, description="Enable composition revisions")
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    resource_limits: Dict[str, str] = Field(default_factory=lambda: {"cpu": "100m", "memory": "512Mi"}, description="Resource limits for Crossplane")
    resource_requests: Dict[str, str] = Field(default_factory=lambda: {"cpu": "100m", "memory": "256Mi"}, description="Resource requests for Crossplane")
    provider_configs: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific configurations")
    compositions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of compositions")
    composite_resources: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of composite resources")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "CrossplaneConfig":
        """
        Merge user configuration with defaults.

        This method takes a user-provided configuration dictionary and merges it
        with the default configuration values defined in this class.

        Args:
            user_config (Dict[str, Any]): The user-provided configuration.

        Returns:
            CrossplaneConfig: A new instance of CrossplaneConfig with merged settings.
        """
        config = cls()
        for key, value in user_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                log.warn(f"Unknown configuration key '{key}' in crossplane config.")
        return config
