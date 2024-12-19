# ./modules/kubernetes/components/prometheus/types.py
"""
Prometheus component types.

TODO:
- Migrate, add, and complete types for Prometheus component.
"""
from typing import Optional, Dict, Any, List
from pydantic import Field
from ...types import KubernetesSubmoduleConfig
from pulumi import log


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

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "PrometheusConfig":
        """Merge user configuration with defaults."""
        config = cls()
        for key, value in user_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                log.warn(f"Unknown configuration key '{key}' in prometheus config.")
        return config
