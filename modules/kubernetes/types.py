# ./modules/kubernetes/types.py

"""
Kubernetes module shared types and interfaces.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone

from ..core.types import ComplianceConfig
from .components.flux.types import FluxConfig
from .components.prometheus.types import PrometheusConfig
from .components.crossplane.types import CrossplaneConfig

class KubernetesMetadata(BaseModel):
    """Base metadata configuration for Kubernetes resources."""
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Kubernetes labels to apply to resources"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Kubernetes annotations to apply to resources"
    )
    name_prefix: Optional[str] = Field(
        default=None,
        description="Prefix to apply to resource names"
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Target namespace for resources"
    )

class ResourceRequirements(BaseModel):
    """Kubernetes resource requirements configuration."""
    limits: Dict[str, str] = Field(
        default_factory=lambda: {"cpu": "100m", "memory": "128Mi"}
    )
    requests: Dict[str, str] = Field(
        default_factory=lambda: {"cpu": "50m", "memory": "64Mi"}
    )

class KubernetesSubmoduleConfig(BaseModel):
    """Base configuration for Kubernetes submodules."""
    enabled: bool = Field(
        default=False,
        description="Whether this submodule is enabled"
    )
    namespace: str = Field(
        default="default",
        description="Target namespace for this submodule"
    )
    version: str = Field(
        default="latest",
        description="Version of the submodule to deploy"
    )
    metadata: KubernetesMetadata = Field(
        default_factory=KubernetesMetadata,
        description="Metadata configuration for this submodule"
    )
    resources: ResourceRequirements = Field(
        default_factory=ResourceRequirements,
        description="Resource requirements for this submodule"
    )
    cluster_selector: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Labels to select which clusters to deploy to"
    )
    deployment_strategy: str = Field(
        default="parallel",
        description="Deploy to clusters in 'parallel' or 'sequential'"
    )
    timeout: int = Field(
        default=300,
        description="Deployment timeout in seconds"
    )
    retry_limit: int = Field(
        default=3,
        description="Number of retry attempts for failed operations"
    )

    @validator('deployment_strategy')
    def validate_strategy(cls, v):
        if v not in ['parallel', 'sequential']:
            raise ValueError("deployment_strategy must be 'parallel' or 'sequential'")
        return v

    class Config:
        arbitrary_types_allowed = True

class ComponentStatus(BaseModel):
    """Status information for a component deployment."""
    state: str = Field(
        default="pending",
        description="Current state of the component (pending, running, completed, failed)"
    )
    message: Optional[str] = Field(
        default=None,
        description="Status message or error details"
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    end_time: Optional[datetime] = None
    resources: List[str] = Field(
        default_factory=list,
        description="List of created resource IDs"
    )

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
                "success_rate": (self.successful_clusters / self.total_clusters * 100)
                               if self.total_clusters > 0 else 0,
                "duration_seconds": self.duration
            },
            "metadata": self.metadata
        }

class KubernetesConfig(BaseModel):
    """Root Kubernetes configuration."""
    provider_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Kubernetes provider configuration"
    )
    global_metadata: KubernetesMetadata = Field(
        default_factory=KubernetesMetadata,
        description="Global metadata applied to all resources"
    )
    compliance: ComplianceConfig = Field(
        default_factory=ComplianceConfig,
        description="Compliance configuration"
    )
    prometheus: Optional[PrometheusConfig] = Field(
        default_factory=PrometheusConfig,
        description="Prometheus component configuration"
    )
    flux: Optional[FluxConfig] = Field(
        default_factory=FluxConfig,
        description="Flux component configuration"
    )
    crossplane: Optional[CrossplaneConfig] = Field(
        default_factory=CrossplaneConfig,
        description="Crossplane component configuration"
    )
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
