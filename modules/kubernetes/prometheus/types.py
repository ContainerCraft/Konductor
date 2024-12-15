# ./modules/kubernetes/prometheus/types.py

"""
Defines the data structure for the Prometheus module configuration.
"""

from typing import Optional, Dict, Any
from pydantic import Field
from ..types import KubernetesConfig
from pulumi import log


class PrometheusConfig(KubernetesConfig):
    """Prometheus module configuration."""

    enabled: bool = Field(default=False)
    namespace: str = Field(default="monitoring")
    version: Optional[str] = Field(default=None)
    openunison_enabled: bool = Field(default=False)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

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
                log.warn(
                    f"Unknown configuration key '{key}' in prometheus config."
                )
        return config
