# modules/kubernetes/flux/types.py
from typing import Optional, Dict, Any, List
from pydantic import Field

from pulumi import log

from ..types import KubernetesConfig

class FluxConfig(KubernetesConfig):
    """Flux module configuration."""

    namespace: str = Field(default="flux-system")
    version: Optional[str] = Field(default=None)
    git_repository: str = Field(...)  # Required
    git_branch: str = Field(default="main")
    git_path: str = Field(default="./")
    interval: str = Field(default="1m")
    components: List[str] = Field(
        default=["source-controller", "kustomize-controller", "helm-controller", "notification-controller"]
    )

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
