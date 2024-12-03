# ./modules/core/deployment.py
from typing import List, Any
from pulumi import log

from modules.core.types import InitializationConfig
from modules.core.interfaces import ModuleInterface
from modules.core.exceptions import ModuleDeploymentError


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

    def deploy_modules(self, modules_to_deploy: List[str]) -> None:
        for module_name in modules_to_deploy:
            try:
                module_class = self.load_module(module_name)
                module_config = self.config_manager.get_module_config(module_name)

                # Add compliance config to module config
                module_config["compliance"] = self.init_config.compliance_config.model_dump()

                module_instance = module_class(init_config=self.init_config)
                result = module_instance.deploy(module_config)

                if result.success:
                    self.modules_metadata[module_name] = result.metadata
                else:
                    raise ModuleDeploymentError(f"Module {module_name} deployment failed.")
            except Exception as e:
                raise ModuleDeploymentError(f"Error deploying module {module_name}: {str(e)}") from e

    # Dynamically load module classes from modules/<module_name>/deployment.py
    # This allows us to maintain a shared interface for all modules while
    # still allowing each module to be implemented independently
    # (e.g. AWS, GCP, Azure, Kubernetes, etc.)
    def load_module(self, module_name: str) -> ModuleInterface:
        """
        Dynamically load module classes from modules/<module_name>/deployment.py
        """
        try:
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
