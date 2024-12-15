# ./modules/kubernetes/deployment.py
"""
Kubernetes submodule deployment handler
"""
from typing import Dict, Any, List, Optional
import pulumi_kubernetes as k8s
import pulumi
from pulumi import log
from datetime import datetime, timezone

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
        """Deploy Kubernetes resources to all available clusters."""
        try:
            registry = KubernetesProviderRegistry()
            providers = registry.list_providers()

            if not providers:
                log.warn("No Kubernetes providers available - skipping deployment")
                return ModuleDeploymentResult(
                    success=True,
                    version="0.0.1",
                    metadata={"status": "no_providers_available"}
                )

            # Simple provider count
            log.info(f"Found {len(providers)} Kubernetes clusters for deployment")

            # List enabled modules
            enabled_submodules = []
            if config.get("prometheus", {}).get("enabled"): enabled_submodules.append("prometheus")
            if config.get("flux", {}).get("enabled"): enabled_submodules.append("flux")
            if config.get("crossplane", {}).get("enabled"): enabled_submodules.append("crossplane")
            log.info(f"Enabled modules: {', '.join(enabled_submodules)}")

            # List target clusters simply
            for provider_id, context in providers.items():
                log.info(f"Target cluster: {context.cluster_name} ({context.environment})")

            # Create deployment summary for metadata
            deployment_summary = {
                "total_clusters": len(providers),
                "clusters": [
                    {
                        "name": ctx.cluster_name,
                        "platform": ctx.platform,
                        "environment": ctx.environment,
                        "region": ctx.region,
                        "provider_id": pid,
                        "target_modules": enabled_submodules
                    }
                    for pid, ctx in providers.items()
                ],
                "enabled_modules": enabled_submodules
            }

            deployment_results = {}
            all_resources = []
            failed_deployments = []

            # Deploy to each cluster
            for provider_id, context in providers.items():
                try:
                    log.info(f"Starting deployment to cluster: {context.cluster_name}")

                    # Initialize cluster metadata
                    cluster_metadata = {
                        "name": context.cluster_name,
                        "platform": context.platform,
                        "environment": context.environment,
                        "region": context.region,
                        "provider_id": provider_id,
                        "submodules": {},
                        "status": "success"
                    }

                    # Deploy each enabled submodule
                    submodules = {
                        "prometheus": (config.get("prometheus", {}).get("enabled"), self._deploy_prometheus),
                        "flux": (config.get("flux", {}).get("enabled"), self._deploy_flux),
                        "crossplane": (config.get("crossplane", {}).get("enabled"), self._deploy_crossplane)
                    }

                    for submodule_name, (enabled, deploy_func) in submodules.items():
                        if enabled:
                            log.info(f"Deploying {submodule_name} to cluster {context.cluster_name}")
                            submodule_config = config.get(submodule_name, {})

                            result = deploy_func(
                                provider=context.provider,
                                config=submodule_config,
                                context=context
                            )

                            if result:
                                all_resources.extend(result.get("resources", []))
                                cluster_metadata["submodules"][submodule_name] = {
                                    "status": "success",
                                    "metadata": result.get("metadata", {}),
                                    "version": submodule_config.get("version")
                                }
                            else:
                                cluster_metadata["submodules"][submodule_name] = {
                                    "status": "failed",
                                    "error": f"Failed to deploy {submodule_name}"
                                }
                                cluster_metadata["status"] = "partial_failure"

                    deployment_results[provider_id] = cluster_metadata

                except Exception as e:
                    error_msg = f"Failed to deploy to cluster {context.cluster_name}: {str(e)}"
                    log.error(error_msg)
                    failed_deployments.append({
                        "cluster": context.cluster_name,
                        "provider_id": provider_id,
                        "error": error_msg
                    })
                    deployment_results[provider_id] = {
                        **cluster_metadata,
                        "status": "failed",
                        "error": error_msg
                    }

            # Determine overall success
            success = len(failed_deployments) == 0
            status = "success" if success else "partial_failure" if deployment_results else "failed"

            return ModuleDeploymentResult(
                success=success,
                version="0.0.1",
                resources=all_resources,
                metadata={
                    "status": status,
                    "clusters": deployment_results,
                    "total_clusters": len(providers),
                    "successful_clusters": len(providers) - len(failed_deployments),
                    "failed_deployments": failed_deployments,
                    "deployment_timestamp": datetime.now(timezone.utc).isoformat(),
                    "deployment_summary": deployment_summary
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

            # Add cluster-specific metadata to config
            flux_config = config.copy()
            flux_config.setdefault("labels", {}).update({
                "cluster-name": context.cluster_name,
                "platform": context.platform,
                "environment": context.environment,
                "region": context.region,
            })

            result = module.deploy(flux_config)
            return {
                "resources": result.resources,
                "metadata": {
                    **result.metadata,
                    "cluster_context": {
                        "name": context.cluster_name,
                        "platform": context.platform,
                        "environment": context.environment,
                        "region": context.region,
                    },
                    "components": flux_config.get("components", []),
                    "reconcile_interval": flux_config.get("reconcile_interval"),
                    "storage_config": {
                        "class": flux_config.get("storage_class"),
                        "size": flux_config.get("storage_size"),
                    }
                }
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

            # Add cluster-specific metadata to config
            crossplane_config = config.copy()
            crossplane_config.setdefault("labels", {}).update({
                "cluster-name": context.cluster_name,
                "platform": context.platform,
                "environment": context.environment,
                "region": context.region,
            })

            # Add provider-specific configurations
            if context.platform == "aws":
                crossplane_config.setdefault("provider_configs", {}).update({
                    "aws": {
                        "region": context.region,
                        "environment": context.environment,
                    }
                })

            result = module.deploy(crossplane_config)
            return {
                "resources": result.resources,
                "metadata": {
                    **result.metadata,
                    "cluster_context": {
                        "name": context.cluster_name,
                        "platform": context.platform,
                        "environment": context.environment,
                        "region": context.region,
                    },
                    "providers": crossplane_config.get("providers", []),
                    "provider_versions": {
                        "aws": crossplane_config.get("aws_provider_version"),
                        "kubernetes": crossplane_config.get("kubernetes_provider_version"),
                    },
                    "features": {
                        "external_secret_stores": crossplane_config.get("enable_external_secret_stores"),
                        "composition_revisions": crossplane_config.get("enable_composition_revisions"),
                    }
                }
            }
        except Exception as e:
            log.error(f"Failed to deploy Crossplane: {str(e)}")
            return None

    def _validate_provider(self, context: KubernetesProviderContext) -> List[str]:
        """Validate provider configuration."""
        errors = []

        if not context.provider:
            errors.append(f"No valid provider for cluster {context.cluster_name}")
            return errors

        try:
            # Test provider connectivity
            namespace = k8s.core.v1.Namespace(
                f"test-{context.cluster_name}",
                metadata={
                    "name": f"test-{context.cluster_name}",
                },
                opts=pulumi.ResourceOptions(provider=context.provider, protect=False)
            )
        except Exception as e:
            errors.append(f"Failed to validate provider for cluster {context.cluster_name}: {str(e)}")

        return errors
