# ./modules/kubernetes/components/flux/types.py
"""
Flux component types.
"""
from typing import Optional, Dict, Any, List
from pydantic import Field

from pulumi import log
from ...types import KubernetesSubmoduleConfig


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
