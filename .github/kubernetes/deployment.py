# ./modules/kubernetes/deployment.py
"""
Kubernetes module deployment handler.
"""
from typing import Dict, Any, List, Optional, Type
import pulumi_kubernetes as k8s
from pulumi import log
from datetime import datetime, timezone

from ..core.interfaces import ModuleInterface, ModuleDeploymentResult
from ..core.types import InitializationConfig
from .providers import KubernetesProvider, KubernetesProviderRegistry
from .types import (
    KubernetesConfig,
    ComponentStatus,
    ClusterDeploymentStatus,
    DeploymentResult,
    KubernetesProviderContext
)

# Import component types
from .components.prometheus.types import PrometheusConfig
from .components.flux.types import FluxConfig
from .components.crossplane.types import CrossplaneConfig

from modules.core.exceptions import ModuleDeploymentError

class KubernetesModule(ModuleInterface):
    """Kubernetes module implementation."""

    def __init__(self, init_config: InitializationConfig):
        self.name = "kubernetes"
        self.init_config = init_config
        self._provider: Optional[KubernetesProvider] = None
        self.registry = KubernetesProviderRegistry()

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

    def _load_component(self, component_name: str) -> Any:
        """
        Dynamically load a component module.

        Args:
            component_name: Name of the component to load

        Returns:
            Component class
        """
        try:
            if component_name == "prometheus":
                from .components.prometheus.deployment import PrometheusComponent
                return PrometheusComponent
            elif component_name == "flux":
                from .components.flux.deployment import FluxComponent
                return FluxComponent
            elif component_name == "crossplane":
                from .components.crossplane.deployment import CrossplaneComponent
                return CrossplaneComponent
            else:
                raise ValueError(f"Unknown component: {component_name}")
        except ImportError as e:
            log.error(f"Failed to load component {component_name}: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error loading component {component_name}: {str(e)}")
            raise

    def _deploy_component(
        self,
        component_name: str,
        config: Dict[str, Any],
        provider: k8s.Provider,
        context: KubernetesProviderContext
    ) -> Optional[Dict[str, Any]]:
        """
        Deploy a specific component.

        Args:
            component_name: Name of the component to deploy
            config: Component configuration
            provider: Kubernetes provider
            context: Provider context

        Returns:
            Optional[Dict[str, Any]]: Deployment result
        """
        try:
            # Load and initialize component
            component_class = self._load_component(component_name)
            component = component_class(init_config=self.init_config)
            component.set_provider(KubernetesProvider(provider))

            # Add cluster-specific metadata
            config.setdefault("metadata", {}).setdefault("labels", {}).update({
                "cluster-name": context.cluster_name,
                "platform": context.platform,
                "environment": context.environment,
                "region": context.region,
            })

            # Deploy component
            result = component.deploy(config)

            if result.success:
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
            return None

        except Exception as e:
            log.error(f"Failed to deploy {component_name}: {str(e)}")
            return None

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy Kubernetes resources to available clusters."""
        try:
            # Early return if kubernetes is disabled
            if not config.get("enabled", False):
                log.info("Kubernetes module is disabled - skipping deployment")
                return ModuleDeploymentResult(
                    success=True,
                    version="0.0.0",
                    metadata={"status": "disabled"}
                )

            providers = self.registry.list_providers()

            if not providers:
                log.warn("No Kubernetes providers available - skipping deployment")
                return ModuleDeploymentResult(
                    success=True,
                    version="0.0.1",
                    metadata={"status": "no_providers_available"}
                )

            # Get enabled components
            enabled_components = []
            if config.get("prometheus", {}).get("enabled"):
                enabled_components.append("prometheus")
            if config.get("flux", {}).get("enabled"):
                enabled_components.append("flux")
            if config.get("crossplane", {}).get("enabled"):
                enabled_components.append("crossplane")

            log.info(f"Found {len(providers)} clusters for deployment")
            log.info(f"Enabled components: {', '.join(enabled_components)}")

            # Create deployment summary
            deployment_summary = {
                "total_clusters": len(providers),
                "clusters": [
                    {
                        "name": ctx.cluster_name,
                        "platform": ctx.platform,
                        "environment": ctx.environment,
                        "region": ctx.region,
                        "provider_id": pid,
                        "target_components": enabled_components
                    }
                    for pid, ctx in providers.items()
                ],
                "enabled_components": enabled_components
            }

            deployment_results = {}
            all_resources = []
            failed_deployments = []

            # Deploy to each cluster
            for provider_id, context in providers.items():
                try:
                    log.info(f"Starting deployment to cluster: {context.cluster_name}")

                    cluster_metadata = {
                        "name": context.cluster_name,
                        "platform": context.platform,
                        "environment": context.environment,
                        "region": context.region,
                        "provider_id": provider_id,
                        "components": {},
                        "status": "success"
                    }

                    # Deploy each enabled component
                    for component_name in enabled_components:
                        component_config = config.get(component_name, {})
                        result = self._deploy_component(
                            component_name,
                            component_config,
                            context.provider,
                            context
                        )

                        if result:
                            all_resources.extend(result["resources"])
                            cluster_metadata["components"][component_name] = {
                                "status": "success",
                                "metadata": result["metadata"],
                                "version": component_config.get("version")
                            }
                        else:
                            cluster_metadata["components"][component_name] = {
                                "status": "failed",
                                "error": f"Failed to deploy {component_name}"
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

class KubernetesModuleLoader:
    """Handles loading of Kubernetes submodules."""

    @staticmethod
    def load_submodule(config: Dict[str, Any]) -> Type[ModuleInterface]:
        """
        Load appropriate kubernetes submodule based on configuration.

        Args:
            config: Kubernetes module configuration

        Returns:
            Type[ModuleInterface]: The module class to instantiate

        Raises:
            ValueError: If no enabled submodule is found
        """
        try:
            # Check for enabled submodules in order of priority
            if config.get("prometheus", {}).get("enabled"):
                from .components.prometheus.deployment import PrometheusComponent
                log.info("Loading Prometheus component")
                return PrometheusComponent

            if config.get("crossplane", {}).get("enabled"):
                from .components.crossplane.deployment import CrossplaneComponent
                log.info("Loading Crossplane component")
                return CrossplaneComponent

            if config.get("flux", {}).get("enabled"):
                from .components.flux.deployment import FluxComponent
                log.info("Loading Flux component")
                return FluxComponent

            raise ValueError("No enabled Kubernetes submodules found in configuration")

        except ImportError as e:
            log.error(f"Failed to import Kubernetes submodule: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error loading Kubernetes submodule: {str(e)}")
            raise

class KubernetesManager:
    """Manages Kubernetes deployments and providers."""

    def __init__(self, init_config: InitializationConfig):
        self.init_config = init_config
        self.registry = KubernetesProviderRegistry()
        self._provider = None

    def deploy_submodule(self, submodule_name: str, submodule_config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy a Kubernetes submodule using the component system."""
        try:
            # Use existing component loading logic
            component_class = self._load_component(submodule_name)
            component = component_class(self.init_config)

            if self._provider:
                component.set_provider(KubernetesProvider(self._provider))

            return component.deploy(submodule_config)

        except Exception as e:
            raise ModuleDeploymentError(f"Error deploying kubernetes submodule {submodule_name}: {str(e)}")

    def set_provider(self, provider: Any) -> None:
        """Set the kubernetes provider."""
        self._provider = provider
