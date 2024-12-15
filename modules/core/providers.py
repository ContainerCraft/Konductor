# modules/core/providers.py
from typing import Dict, Optional, Any
from dataclasses import dataclass
from pulumi import ResourceOptions, Output
import pulumi_kubernetes as k8s


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
    """Thread-safe singleton registry for kubernetes providers."""

    _instance = None
    _providers: Dict[str, KubernetesProviderContext]
    _default_provider: Optional[str]

    def __new__(cls):
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
        metadata: Dict[str, Any] = None,
        make_default: bool = False,
    ) -> None:
        """Register a kubernetes provider with context."""
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

    def get_default_provider(self) -> Optional[KubernetesProviderContext]:
        """Get the default provider if one is set."""
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None

    def get_providers_by_platform(self, platform: str) -> Dict[str, KubernetesProviderContext]:
        """Get all providers for a specific platform."""
        return {k: v for k, v in self._providers.items() if v.platform == platform}

    def get_providers_by_environment(self, environment: str) -> Dict[str, KubernetesProviderContext]:
        """Get all providers for a specific environment."""
        return {k: v for k, v in self._providers.items() if v.environment == environment}

    def get_providers_by_region(self, region: str) -> Dict[str, KubernetesProviderContext]:
        """Get all providers in a specific region."""
        return {k: v for k, v in self._providers.items() if v.region == region}

    def list_providers(self) -> Dict[str, KubernetesProviderContext]:
        """Get all registered providers."""
        return self._providers.copy()

    def remove_provider(self, provider_id: str) -> None:
        """Remove a provider from the registry."""
        if provider_id in self._providers:
            if self._default_provider == provider_id:
                self._default_provider = None
            del self._providers[provider_id]

    def set_default_provider(self, provider_id: str) -> None:
        """Set the default provider."""
        if provider_id in self._providers:
            self._default_provider = provider_id
        else:
            raise ValueError(f"Provider {provider_id} not found in registry")

    def get_provider_metadata(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific provider."""
        if context := self._providers.get(provider_id):
            return context.metadata
        return None

    def update_provider_metadata(self, provider_id: str, metadata: Dict[str, Any]) -> None:
        """Update metadata for a specific provider."""
        if context := self._providers.get(provider_id):
            context.metadata.update(metadata)
