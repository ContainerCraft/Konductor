# modules/kubernetes/flux/types.py
from typing import Optional, Dict, Any, List
from pydantic import Field

from pulumi import log

from ..types import KubernetesConfig

class FluxConfig(KubernetesConfig):
    """Flux module configuration."""

    namespace: str = Field(default="flux-system")
    version: Optional[str] = Field(default="2.x")
    operator_version: Optional[str] = Field(default="latest")
    components: List[str] = Field(
        default=[
            "source-controller",
            "kustomize-controller",
            "helm-controller",
            "notification-controller",
        ]
    )
    storage_class: str = Field(default="standard")
    storage_size: str = Field(default="10Gi")
    network_policy: bool = Field(default=True)
    multitenant: bool = Field(default=False)
    cluster_domain: str = Field(default="cluster.local")
    reconcile_interval: str = Field(default="1h")
    reconcile_timeout: str = Field(default="3m")
    concurrent_reconciles: int = Field(default=10)
    requeue_dependency_interval: str = Field(default="5s")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "FluxConfig":
        """Merge user configuration with defaults."""
        config = cls()
        for key, value in user_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                log.warn(f"Unknown configuration key '{key}' in flux config.")
        return config
