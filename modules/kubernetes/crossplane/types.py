# modules/kubernetes/crossplane/types.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ..types import KubernetesConfig
from pulumi import log


class ProviderConfig(BaseModel):
    """Configuration for a Crossplane provider."""
    name: str
    version: str
    config: Dict[str, Any] = Field(default_factory=dict)


class CrossplaneConfig(KubernetesConfig):
    """Crossplane module configuration."""

    namespace: str = Field(default="crossplane-system")
    version: str = Field(default="1.14.1")
    providers: List[str] = Field(default=["provider-aws", "provider-kubernetes"])
    aws_provider_version: str = Field(default="v0.43.1")
    kubernetes_provider_version: str = Field(default="v0.10.0")
    aws_provider_config: Dict[str, Any] = Field(default_factory=dict)
    enable_external_secret_stores: bool = Field(default=True)
    enable_composition_revisions: bool = Field(default=True)
    metrics_enabled: bool = Field(default=True)
    debug_mode: bool = Field(default=False)
    resource_limits: Dict[str, str] = Field(
        default_factory=lambda: {
            "cpu": "100m",
            "memory": "512Mi"
        }
    )
    resource_requests: Dict[str, str] = Field(
        default_factory=lambda: {
            "cpu": "100m",
            "memory": "256Mi"
        }
    )

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "CrossplaneConfig":
        """Merge user configuration with defaults."""
        config = cls()
        for key, value in user_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                log.warn(f"Unknown configuration key '{key}' in crossplane config.")
        return config
