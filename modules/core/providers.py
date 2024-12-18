# ./modules/core/providers.py
"""
Core module provider registration and management.

Contains minimum viable global provider registry for modules to register and retrieve
platform providers for chaining together module deployments and supporting downstream
platform provider dependencies.

TODO: Develop an agnostic, extensible, intuitive, modular, and scalable provider registry architecture and implementation strategy.
TODO: Implement provider agnostic interface for modules to register and retrieve providers.
TODO: Implement AWS module and Kubernetes module provider registry publishing and retrival utilizing the provider agnostic interface.
"""

from typing import Any, Dict


# TODO: Evaluate if core module should be responsible for registering Kubernetes providers.
# RECOMMEND: Kubernetes module should be responsible for registering Kubernetes providers.
# CONSIDER: Core module may need a global provider agnostic registry for modules to registr
# platform providers for use in downstream modules.
def register_kubernetes_provider(
    self,
    provider_id: str,
    provider: Any,
    cluster_name: str,
    platform: str,
    environment: str,
    region: str,
    metadata: Dict[str, Any] = None,
    make_default: bool = False
) -> None:
    """Register a kubernetes provider."""
    self.k8s_registry.register_provider(
        provider_id=provider_id,
        provider=provider,
        cluster_name=cluster_name,
        platform=platform,
        environment=environment,
        region=region,
        metadata=metadata,
        make_default=make_default
    )
