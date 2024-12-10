# ./modules/kubernetes/provider.py
"""
Kubernetes submodule authentication provider
"""
# modules/kubernetes/provider.py
from typing import Optional
import pulumi_kubernetes as k8s
from pulumi import ResourceOptions, log


class KubernetesProvider:
    """Manages Kubernetes provider initialization and configuration."""

    def __init__(self, k8s_provider: Optional[k8s.Provider] = None):
        """
        Initialize Kubernetes provider.

        Args:
            k8s_provider: Optional existing provider (e.g. from EKS)
        """
        self._provider = k8s_provider

    @property
    def provider(self) -> k8s.Provider:
        """Get the Kubernetes provider instance."""
        if not self._provider:
            raise RuntimeError("Kubernetes Provider not initialized")
        return self._provider
