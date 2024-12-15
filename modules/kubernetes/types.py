# ./modules/kubernetes/types.py
"""
Kubernetes submodule shared types
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from ..core.types import ComplianceConfig

class KubernetesSubmoduleConfig(BaseModel):
    """Base configuration for Kubernetes submodules."""
    enabled: bool = False
    namespace: str = "default"
    version: str = "latest"

class PrometheusConfig(KubernetesSubmoduleConfig):
    """Prometheus specific configuration."""
    enabled: bool = False
    namespace: str = "monitoring"
    version: str = "45.7.1"
    openunison_enabled: bool = False
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    storage_class: Optional[str] = None
    storage_size: Optional[str] = None
    retention_size: Optional[str] = None
    retention_time: Optional[str] = None
    replicas: Optional[int] = None
    resources: Optional[Dict[str, Any]] = Field(default_factory=dict)
    node_selector: Optional[Dict[str, str]] = Field(default_factory=dict)
    tolerations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    affinity: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FluxConfig(KubernetesSubmoduleConfig):
    """Flux specific configuration."""
    enabled: bool = False
    namespace: str = "flux-system"
    version: str = "2.x"
    operator_version: str = "0.10.0"
    storage_class: str = "gp2"
    storage_size: str = "10Gi"
    network_policy: bool = True
    multitenant: bool = False
    cluster_domain: str = "cluster.local"
    reconcile_interval: str = "1h"
    reconcile_timeout: str = "3m"
    concurrent_reconciles: int = 10
    requeue_dependency_interval: str = "5s"
    components: List[str] = Field(default_factory=list)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

class CrossplaneConfig(KubernetesSubmoduleConfig):
    """Crossplane specific configuration."""
    enabled: bool = False
    namespace: str = "crossplane-system"
    version: str = "1.18.0"
    providers: List[str] = Field(default_factory=list)
    aws_provider_version: str = "v0.43.1"
    kubernetes_provider_version: str = "v0.10.0"
    enable_external_secret_stores: bool = True
    enable_composition_revisions: bool = True
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    provider_configs: Optional[Dict[str, Any]] = Field(default_factory=dict)

class KubernetesConfig(BaseModel):
    """Root Kubernetes configuration."""
    prometheus: Optional[PrometheusConfig] = Field(default_factory=PrometheusConfig)
    flux: Optional[FluxConfig] = Field(default_factory=FluxConfig)
    crossplane: Optional[CrossplaneConfig] = Field(default_factory=CrossplaneConfig)

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "KubernetesConfig":
        """Merge user configuration with defaults."""
        config = cls()
        for key, value in user_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
