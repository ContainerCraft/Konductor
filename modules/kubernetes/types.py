# ./modules/kubernetes/types.py
"""
Kubernetes submodule shared types
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ..core.types import ComplianceConfig

class KubernetesConfig(BaseModel):
    """Base Kubernetes configuration."""

    enabled: bool = Field(default=True)
    provider_type: str = Field(default="eks")  # eks, kind, etc
    namespace: str = Field(default="default")
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, Any] = Field(default_factory=dict)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "KubernetesConfig":
        """Merge user configuration with defaults."""
        config = cls()
        for key, value in user_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
