# ./modules/kubernetes/deployment.py
"""
Kubernetes submodule deployment handler
"""
from typing import Dict, Any, List, Optional
from pulumi import log
from ..core.interfaces import ModuleInterface, ModuleDeploymentResult
from ..core.types import InitializationConfig
from .provider import KubernetesProvider
from .types import KubernetesConfig


class KubernetesModule(ModuleInterface):
    """Base Kubernetes module implementation."""

    def __init__(self, init_config: InitializationConfig):
        self.name = "kubernetes"
        self.init_config = init_config
        self._provider: Optional[KubernetesProvider] = None

    def set_provider(self, provider: KubernetesProvider) -> None:
        """Set the Kubernetes provider."""
        self._provider = provider

    @property
    def provider(self) -> KubernetesProvider:
        if not self._provider:
            raise RuntimeError("Kubernetes provider not initialized")
        return self._provider

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Kubernetes configuration."""
        try:
            if config is None:
                config = {}
            KubernetesConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy Kubernetes resources."""
        raise NotImplementedError("Subclasses must implement deploy()")
