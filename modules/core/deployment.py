# ./modules/core/deployment.py
from typing import List, Any, Dict
from pulumi import log

from modules.core.types import InitializationConfig
from modules.core.interfaces import ModuleInterface
from modules.core.exceptions import ModuleDeploymentError
from modules.kubernetes.provider import KubernetesProvider
from modules.core.providers import KubernetesProviderRegistry


class DeploymentManager:
    """
    Deployment Manager

    Manages the deployment of modules. Supports dynamic module loading from
    modules/<module_name>/deployment.py and storing metadata for each module
    that can be exported to the stack outputs consolidating all module outputs
    for use in downstream modules or external business logic and analytics systems.
    """

    def __init__(self, init_config: InitializationConfig, config_manager: Any):
        self.init_config = init_config
        self.config_manager = config_manager
        self.modules_metadata = {}
        self.k8s_registry = KubernetesProviderRegistry()
        self.k8s_provider = None

    def deploy_modules(self, modules_to_deploy: List[str]) -> None:
        for module_name in modules_to_deploy:
            try:
                # Standard module deployment for all modules including kubernetes
                module_class = self.load_module(module_name)
                module_config = self.config_manager.get_module_config(module_name)
                module_config["compliance"] = self.init_config.compliance_config.model_dump()

                module_instance = module_class(init_config=self.init_config)
                result = module_instance.deploy(module_config)

                if result.success:
                    self.modules_metadata[module_name] = result.metadata
                    if module_name == "aws" and "k8s_provider" in result.metadata:
                        self.k8s_provider = result.metadata["k8s_provider"]
                else:
                    raise ModuleDeploymentError(f"Module {module_name} deployment failed.")

            except Exception as e:
                raise ModuleDeploymentError(f"Error deploying module {module_name}: {str(e)}") from e

    def deploy_k8s_submodule(self, submodule_name: str, submodule_config: Dict[str, Any]) -> None:
        """Deploy a Kubernetes submodule."""
        try:
            # Load the submodule
            if submodule_name == "prometheus":
                module = __import__("modules.kubernetes.prometheus.deployment", fromlist=[""])
                module_class = getattr(module, "PrometheusModule")
            elif submodule_name == "flux":
                module = __import__("modules.kubernetes.flux.deployment", fromlist=[""])
                module_class = getattr(module, "FluxModule")
            elif submodule_name == "crossplane":
                module = __import__("modules.kubernetes.crossplane.deployment", fromlist=[""])
                module_class = getattr(module, "CrossplaneModule")
            else:
                raise ValueError(f"Unknown kubernetes submodule: {submodule_name}")

            # Initialize and configure the module
            module_instance = module_class(init_config=self.init_config)
            if self.k8s_provider:
                module_instance.set_provider(KubernetesProvider(self.k8s_provider))

            # Deploy the submodule
            result = module_instance.deploy(submodule_config)
            if result.success:
                self.modules_metadata[f"kubernetes_{submodule_name}"] = result.metadata
            else:
                raise ModuleDeploymentError(f"Kubernetes submodule {submodule_name} deployment failed.")

        except Exception as e:
            raise ModuleDeploymentError(f"Error deploying kubernetes submodule {submodule_name}: {str(e)}")

    def get_k8s_provider(self):
        """Get the Kubernetes provider if available"""
        return self.k8s_provider

    # Dynamically load module classes from modules/<module_name>/deployment.py
    # This allows us to maintain a shared interface for all modules while
    # still allowing each module to be implemented independently
    # (e.g. AWS, GCP, Azure, Kubernetes, etc.)
    def load_module(self, module_name: str) -> ModuleInterface:
        """
        Dynamically load module classes from modules/<module_name>/deployment.py
        """
        try:
            if module_name == "kubernetes":
                # Get kubernetes config to check which submodule to load
                k8s_config = self.config_manager.get_module_config(module_name)

                # Check for enabled submodules
                # TODO: re-enable dynamic submodule loading without hardcoding submodule names
                if k8s_config.get("prometheus", {}).get("enabled"):
                    # Import and return Prometheus module
                    module = __import__(f"modules.kubernetes.prometheus.deployment", fromlist=[""])
                    module_class = getattr(module, "PrometheusModule")
                    log.info(f"Successfully loaded kubernetes submodule: prometheus")
                    return module_class
                if k8s_config.get("flux", {}).get("enabled"):
                    # Import and return Flux module
                    module = __import__(f"modules.kubernetes.flux.deployment", fromlist=[""])
                    module_class = getattr(module, "FluxModule")
                    log.info(f"Successfully loaded kubernetes submodule: flux")
                    return module_class
                if k8s_config.get("crossplane", {}).get("enabled"):
                    # Import and return Crossplane module
                    module = __import__(f"modules.kubernetes.crossplane.deployment", fromlist=[""])
                    module_class = getattr(module, "CrossplaneModule")
                    log.info(f"Successfully loaded kubernetes submodule: crossplane")
                    return module_class
            else:
                # Standard module loading
                module = __import__(f"modules.{module_name}.deployment", fromlist=[""])
                module_class = getattr(module, f"{module_name.capitalize()}Module")
                log.info(f"Successfully loaded module: {module_name}")
                return module_class

        except ImportError as e:
            log.error(f"Failed to load module {module_name}: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Failed to load module {module_name}: {str(e)}")
            raise

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
