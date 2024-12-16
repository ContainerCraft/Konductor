# ./modules/kubernetes/provider.py
"""
Kubernetes submodule authentication provider
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import pulumi_kubernetes as k8s


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


@dataclass
class KubernetesProviderContext:
    """Kubernetes provider context with metadata."""

    provider: k8s.Provider
    cluster_name: str
    platform: str  # aws, azure, gcp, etc.
    environment: str  # dev, staging, prod, etc.
    region: str
    metadata: Dict[str, Any]


class KubernetesProviderRegistry:
    """Module-wide thread-safe Kubernetes Provider singleton registry."""

    _instance: Optional["KubernetesProviderRegistry"] = None

    def __new__(cls) -> "KubernetesProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {}
            cls._instance._default_provider = None
        return cls._instance

    def register_provider(
        self,
        provider_id: str,
        provider: k8s.Provider,
        cluster_name: str,
        platform: str,
        environment: str,
        region: str,
        metadata: Optional[Dict[str, Any]] = None,
        make_default: bool = False,
    ) -> None:
        """Register a Kubernetes provider with context."""
        context = KubernetesProviderContext(
            provider=provider,
            cluster_name=cluster_name,
            platform=platform,
            environment=environment,
            region=region,
            metadata=metadata or {},
        )
        self._providers[provider_id] = context
        if make_default or not self._default_provider:
            self._default_provider = provider_id

    def get_provider(self, provider_id: str) -> Optional[KubernetesProviderContext]:
        """Get a provider by ID."""
        return self._providers.get(provider_id)

    def get_providers_by_platform(self, platform: str) -> Dict[str, KubernetesProviderContext]:
        """Get all providers for a specific platform."""
        return {k: v for k, v in self._providers.items() if v.platform == platform}

    def get_providers_by_environment(self, environment: str) -> Dict[str, KubernetesProviderContext]:
        """Get all providers for a specific environment."""
        return {k: v for k, v in self._providers.items() if v.environment == environment}
