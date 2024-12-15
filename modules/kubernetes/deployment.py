# ./modules/kubernetes/deployment.py
"""
Kubernetes submodule deployment handler
"""
from typing import Dict, Any, List, Optional
import pulumi_kubernetes as k8s
from pulumi import log

from ..core.interfaces import ModuleInterface, ModuleDeploymentResult
from ..core.types import InitializationConfig
from ..core.providers import KubernetesProviderRegistry, KubernetesProviderContext
from .provider import KubernetesProvider
from .types import KubernetesConfig, PrometheusConfig


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
        try:
            registry = KubernetesProviderRegistry()
            providers = registry.list_providers()

            if not providers:
                log.warn("No Kubernetes providers available - EKS clusters may not be enabled")
                return ModuleDeploymentResult(
                    success=True,
                    version="0.0.1",
                    metadata={"status": "no_providers_available"}
                )

            log.info(f"Found {len(providers)} Kubernetes providers")
            deployed_resources = []
            deployment_metadata = {}

            # Deploy to each available provider
            for provider_id, context in providers.items():
                log.info(f"Deploying to Kubernetes cluster: {context.cluster_name} ({provider_id})")
                cluster_metadata = {
                    "name": context.cluster_name,
                    "platform": context.platform,
                    "environment": context.environment,
                    "region": context.region,
                    "submodules": {}
                }

                # Deploy Prometheus if enabled
                if config.get("prometheus", {}).get("enabled"):
                    log.info(f"Deploying Prometheus to cluster: {context.cluster_name}")
                    prometheus_result = self._deploy_prometheus(
                        provider=context.provider,
                        config=config.get("prometheus", {}),
                        context=context
                    )
                    if prometheus_result:
                        deployed_resources.extend(prometheus_result.get("resources", []))
                        cluster_metadata["submodules"]["prometheus"] = prometheus_result.get("metadata", {})

                # Deploy Flux if enabled
                if config.get("flux", {}).get("enabled"):
                    log.info(f"Deploying Flux to cluster: {context.cluster_name}")
                    flux_result = self._deploy_flux(
                        provider=context.provider,
                        config=config.get("flux", {}),
                        context=context
                    )
                    if flux_result:
                        deployed_resources.extend(flux_result.get("resources", []))
                        cluster_metadata["submodules"]["flux"] = flux_result.get("metadata", {})

                # Deploy Crossplane if enabled
                if config.get("crossplane", {}).get("enabled"):
                    log.info(f"Deploying Crossplane to cluster: {context.cluster_name}")
                    crossplane_result = self._deploy_crossplane(
                        provider=context.provider,
                        config=config.get("crossplane", {}),
                        context=context
                    )
                    if crossplane_result:
                        deployed_resources.extend(crossplane_result.get("resources", []))
                        cluster_metadata["submodules"]["crossplane"] = crossplane_result.get("metadata", {})

                deployment_metadata[provider_id] = cluster_metadata

            log.info(f"Successfully deployed to {len(deployment_metadata)} clusters")
            return ModuleDeploymentResult(
                success=True,
                version="0.0.1",
                resources=deployed_resources,
                metadata={
                    "clusters": deployment_metadata,
                    "total_clusters": len(providers),
                    "successful_deployments": len([
                        cluster for cluster in deployment_metadata.values()
                        if cluster["submodules"]
                    ])
                }
            )

        except Exception as e:
            log.error(f"Kubernetes module deployment failed: {str(e)}")
            raise

    def deploy_to_provider(
        self,
        provider: k8s.Provider,
        config: Dict[str, Any],
        context: KubernetesProviderContext
    ) -> Optional[Dict[str, Any]]:
        """Deploy resources to a specific provider."""
        try:
            deployed_resources = []
            metadata = {}

            # Deploy enabled submodules
            if config.get("prometheus", {}).get("enabled"):
                prometheus_result = self._deploy_prometheus(
                    provider=provider,
                    config=config.get("prometheus", {}),
                    context=context
                )
                if prometheus_result:
                    deployed_resources.extend(prometheus_result.get("resources", []))
                    metadata["prometheus"] = prometheus_result.get("metadata", {})

            if config.get("flux", {}).get("enabled"):
                flux_result = self._deploy_flux(
                    provider=provider,
                    config=config.get("flux", {}),
                    context=context
                )
                if flux_result:
                    deployed_resources.extend(flux_result.get("resources", []))
                    metadata["flux"] = flux_result.get("metadata", {})

            if config.get("crossplane", {}).get("enabled"):
                crossplane_result = self._deploy_crossplane(
                    provider=provider,
                    config=config.get("crossplane", {}),
                    context=context
                )
                if crossplane_result:
                    deployed_resources.extend(crossplane_result.get("resources", []))
                    metadata["crossplane"] = crossplane_result.get("metadata", {})

            return {
                "resources": deployed_resources,
                "metadata": metadata
            }

        except Exception as e:
            log.error(f"Failed to deploy to provider {context.cluster_name}: {str(e)}")
            return None

    def _deploy_prometheus(
        self,
        provider: k8s.Provider,
        config: Dict[str, Any],
        context: KubernetesProviderContext
    ) -> Optional[Dict[str, Any]]:
        """Deploy Prometheus stack."""
        try:
            from .prometheus.deployment import PrometheusModule
            module = PrometheusModule(self.init_config)
            module.set_provider(KubernetesProvider(provider))

            # Ensure config has all fields with defaults
            prometheus_config = PrometheusConfig(**config)

            # Add cluster-specific metadata
            prometheus_config.labels.update({
                "cluster-name": context.cluster_name,
                "platform": context.platform,
                "environment": context.environment,
                "region": context.region,
            })

            result = module.deploy(prometheus_config.dict())
            return {
                "resources": result.resources,
                "metadata": {
                    **result.metadata,
                    "cluster_context": {
                        "name": context.cluster_name,
                        "platform": context.platform,
                        "environment": context.environment,
                        "region": context.region,
                    }
                }
            }
        except Exception as e:
            log.error(f"Failed to deploy Prometheus: {str(e)}")
            return None

    def _deploy_flux(
        self,
        provider: k8s.Provider,
        config: Dict[str, Any],
        context: KubernetesProviderContext
    ) -> Optional[Dict[str, Any]]:
        """Deploy Flux GitOps."""
        try:
            from .flux.deployment import FluxModule
            module = FluxModule(self.init_config)
            module.set_provider(KubernetesProvider(provider))
            result = module.deploy(config)
            return {
                "resources": result.resources,
                "metadata": result.metadata
            }
        except Exception as e:
            log.error(f"Failed to deploy Flux: {str(e)}")
            return None

    def _deploy_crossplane(
        self,
        provider: k8s.Provider,
        config: Dict[str, Any],
        context: KubernetesProviderContext
    ) -> Optional[Dict[str, Any]]:
        """Deploy Crossplane."""
        try:
            from .crossplane.deployment import CrossplaneModule
            module = CrossplaneModule(self.init_config)
            module.set_provider(KubernetesProvider(provider))
            result = module.deploy(config)
            return {
                "resources": result.resources,
                "metadata": result.metadata
            }
        except Exception as e:
            log.error(f"Failed to deploy Crossplane: {str(e)}")
            return None
