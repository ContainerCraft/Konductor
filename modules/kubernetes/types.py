# ./modules/kubernetes/types.py

"""
Kubernetes submodule shared types
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone
from ..core.types import ComplianceConfig

class KubernetesSubmoduleConfig(BaseModel):
    """Base configuration for Kubernetes submodules."""
    enabled: bool = False
    namespace: str = "default"
    version: str = "latest"
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    cluster_selector: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Labels to select which clusters to deploy to"
    )
    deployment_strategy: str = Field(
        default="parallel",
        description="Deploy to clusters in 'parallel' or 'sequential'"
    )

    @validator('deployment_strategy')
    def validate_strategy(cls, v):
        if v not in ['parallel', 'sequential']:
            raise ValueError("deployment_strategy must be 'parallel' or 'sequential'")
        return v

class PrometheusConfig(KubernetesSubmoduleConfig):
    """Prometheus specific configuration."""
    enabled: bool = False
    namespace: str = "monitoring"
    version: str = "45.7.1"
    openunison_enabled: bool = False
    storage_class: Optional[str] = None
    storage_size: Optional[str] = None
    retention_size: Optional[str] = None
    retention_time: Optional[str] = None
    replicas: Optional[int] = None
    resources: Optional[Dict[str, Any]] = Field(default_factory=dict)
    node_selector: Optional[Dict[str, str]] = Field(default_factory=dict)
    tolerations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    affinity: Optional[Dict[str, Any]] = Field(default_factory=dict)
    alertmanager: Optional[Dict[str, Any]] = Field(default_factory=dict)
    grafana: Optional[Dict[str, Any]] = Field(default_factory=dict)

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
    git_repositories: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    kustomizations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    helm_repositories: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

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
    provider_configs: Dict[str, Any] = Field(default_factory=dict)
    compositions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    composite_resources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class ClusterDeploymentStatus(BaseModel):
    """Status of deployment to a specific cluster."""
    cluster_name: str
    provider_id: str
    platform: str
    environment: str
    region: str
    status: str = "pending"  # pending, success, failed, partial_failure
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    submodules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

class KubernetesConfig(BaseModel):
    """Root Kubernetes configuration."""
    prometheus: Optional[PrometheusConfig] = Field(default_factory=PrometheusConfig)
    flux: Optional[FluxConfig] = Field(default_factory=FluxConfig)
    crossplane: Optional[CrossplaneConfig] = Field(default_factory=CrossplaneConfig)
    deployment_timeout: int = Field(
        default=600,
        description="Global deployment timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed deployments"
    )
    cluster_concurrency: int = Field(
        default=4,
        description="Maximum number of concurrent cluster deployments"
    )

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "KubernetesConfig":
        """Merge user configuration with defaults."""
        base_config = cls()

        # Deep merge the configurations
        for key, value in user_config.items():
            if hasattr(base_config, key):
                current_value = getattr(base_config, key)
                if isinstance(current_value, (PrometheusConfig, FluxConfig, CrossplaneConfig)):
                    # Merge submodule configs
                    merged_value = {**current_value.dict(), **(value or {})}
                    setattr(base_config, key, type(current_value)(**merged_value))
                else:
                    setattr(base_config, key, value)

        return base_config

class DeploymentResult(BaseModel):
    """Result of a deployment operation."""
    success: bool
    cluster_results: Dict[str, ClusterDeploymentStatus]
    total_clusters: int
    successful_clusters: int
    failed_clusters: int
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Calculate deployment duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "success": self.success,
            "cluster_results": {
                name: status.dict() for name, status in self.cluster_results.items()
            },
            "statistics": {
                "total_clusters": self.total_clusters,
                "successful_clusters": self.successful_clusters,
                "failed_clusters": self.failed_clusters,
                "success_rate": (self.successful_clusters / self.total_clusters * 100) if self.total_clusters > 0 else 0,
                "duration_seconds": self.duration
            },
            "metadata": self.metadata
        }
