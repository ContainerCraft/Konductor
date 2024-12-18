# ./modules/core/deployment.py

"""
Core module deployment implementation.
"""

from typing import List
from pulumi import log

from modules.core.types import InitializationConfig
from modules.core.interfaces import ModuleInterface
from modules.core.config import ConfigManager


class DeploymentManager:
    """
    Deployment Manager

    Manages the deployment of modules. Supports dynamic module loading from
    modules/<module_name>/deployment.py and storing metadata for each module
    that can be exported to the stack outputs consolidating all module outputs
    for use in downstream modules or external business logic and analytics systems.
    """

    def __init__(self, init_config: InitializationConfig, config_manager: ConfigManager):
        self.init_config = init_config
        self.config_manager = config_manager
        self.modules_metadata = {}

    def deploy_modules(self, modules: List[str]) -> None:
        """Deploy enabled modules."""
        for module_name in modules:
            try:
                # Get module config
                module_config = self.config_manager.get_module_config(module_name)

                # Skip if module is explicitly disabled
                if not module_config.get("enabled", True):
                    log.info(f"Module {module_name} is disabled - skipping")
                    continue

                # Load and deploy module
                module = self.load_module(module_name)
                if module:
                    self._deploy_module(module, module_config)

            except Exception as e:
                log.error(f"Failed to deploy module {module_name}: {str(e)}")
                raise

    # Dynamically load module interface classes from modules/<module_name>/types/__init__.py
    # Dynamically discover module entrypoints from modules/<module_name>/deployment.py
    # This allows for a shared common dynamic discovery and deployment interface for all modules while
    # enabling each module to be loosely coupled, have full autonomy and provenance over module configuration,
    # defaults, and implementation across all cloud providers (e.g. AWS, GCP, Azure, Kubernetes, OpenStack, DigitalOcean, Hetzner, etc.)
    def load_module(self, module_name: str) -> ModuleInterface:
        """
        Dynamically discover and load module interface classes from modules/<module_name>/types/__init__.py
        Dynamically load module entrypoint from modules/<module_name>/deployment.py
        Support checking module and submodule enabled statuses.
        Load module only if the module is enabled.
        Returns the module interface class or None if the module is not enabled.
        """
        try:
            # Verify module is enabled before loading
            module_config = self.config_manager.get_module_config(module_name)
            if not module_config.get("enabled"):
                return None

            # Standard module loading
            # TODO: Implement dynamic module discovery and loading.
            # TODO: Implement support for module and submodule enabled checking.
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
