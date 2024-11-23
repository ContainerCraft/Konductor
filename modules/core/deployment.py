# ../konductor/modules/core/deployment.py
import importlib
import pulumi
from pulumi import log
from typing import List, Dict

from modules.core.types import InitializationConfig
from modules.core.interfaces import ModuleDeploymentResult

class DeploymentManager:
    """
    Manages the deployment of modules based on the configuration.
    """

    def __init__(self, init_config: InitializationConfig):
        self.init_config = init_config
        self.deployed_modules: Dict[str, ModuleDeploymentResult] = {}

    def deploy_modules(self, modules_to_deploy: List[str]) -> None:
        """
        Deploys the enabled modules.

        Args:
            modules_to_deploy: A list of module names to deploy.
        """
        for module_name in modules_to_deploy:
            try:
                self.deploy_module(module_name)
            except Exception as e:
                log.error(f"Failed to deploy module {module_name}: {str(e)}")

    def deploy_module(self, module_name: str) -> None:
        """
        Deploys a single module by dynamically importing and executing its deploy function.

        Args:
            module_name: The name of the module to deploy.
        """
        try:
            # Dynamically import the module's deploy function
            deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
            deploy_func = getattr(deploy_module, "deploy", None)

            if not callable(deploy_func):
                raise AttributeError(f"Module {module_name} does not have a deploy function.")

            # Retrieve the module configuration
            module_config = self.init_config.config.get_object(module_name) or {}

            # Call the deploy function with the necessary arguments
            result = deploy_func(
                config=module_config,
                init_config=self.init_config,
            )

            # Store the deployment result
            self.deployed_modules[module_name] = result

        except ImportError as e:
            log.error(f"Module {module_name} could not be imported: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error deploying module {module_name}: {str(e)}")
            raise
