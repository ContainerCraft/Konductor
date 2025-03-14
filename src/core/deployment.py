# ./src/core/deployment.py

"""
Core module deployment implementation.
"""

from typing import List, Optional, Dict, Any
from importlib import import_module
from pathlib import Path
from pulumi import log

from src.core.types import (
    InitializationConfig,
    ModuleInterface,
    BaseConfigModel,
    ModuleDeploymentResult,
    ModuleLoadError,
)

from src.core.config import ConfigManager


class DeploymentManager:
    """
    Deployment Manager

    Manages the deployment of modules. Supports dynamic module loading from
    modules/<module_name>/deployment.py and storing metadata for each module.
    """

    def __init__(
        self,
        init_config: InitializationConfig,
        config_manager: ConfigManager
    ):
        self.init_config = init_config
        self.config_manager = config_manager
        self.modules_metadata: Dict[str, Dict[str, Any]] = {}
        self._discovered_modules: Dict[str, str] = {}
        self._discover_available_modules()

    def _discover_available_modules(self) -> None:
        """Dynamically discover available modules in the modules directory."""
        try:
            modules_dir = Path(__file__).parent.parent
            for item in modules_dir.iterdir():
                if (
                    item.is_dir()
                    and not item.name.startswith('_')
                    and (item / "deployment.py").exists()
                ):
                    self._discovered_modules[item.name] = str(item / "deployment.py")
                    log.debug(f"Discovered module: {item.name}")
        except Exception as e:
            log.error(f"Module discovery failed: {str(e)}")
            raise ModuleLoadError(f"Failed to discover modules: {str(e)}") from e

    def deploy_modules(self, modules: List[str]) -> None:
        """Deploy enabled modules."""
        for module_name in modules:
            try:
                # Verify module exists
                if module_name not in self._discovered_modules:
                    log.warn(f"Module {module_name} not found - skipping")
                    continue

                # Get module config and check if enabled
                module_config = self.config_manager.get_module_config(module_name)
                if not module_config.get("enabled", True):
                    log.info(f"Module {module_name} is disabled - skipping")
                    continue

                # Load and deploy module
                if module := self.load_module(module_name):
                    self._deploy_module(module, module_config)

            except Exception as e:
                log.error(f"Failed to deploy module {module_name}: {str(e)}")
                raise

    def _deploy_module(self, module: ModuleInterface, config: Dict[str, Any]) -> None:
        """Deploy a single module with its configuration."""
        try:
            # Convert dict config to BaseConfigModel
            module_config = BaseConfigModel(
                enabled=config.get("enabled", False),
                configuration=config
            )

            # Validate module configuration
            if validation_errors := module.validate(module_config):
                raise ValueError(
                    f"Module configuration validation failed: {validation_errors}"
                )

            # Create deployment context
            class ModuleDeploymentContext:
                def get_config(self) -> BaseConfigModel:
                    return module_config

                def deploy(self) -> ModuleDeploymentResult:
                    return module.deploy(self)

            # Deploy module and store metadata
            context = ModuleDeploymentContext()
            if result := module.deploy(context):
                if result.metadata:
                    self.modules_metadata[module.__class__.__name__] = result.metadata

        except Exception as e:
            log.error(f"Failed to deploy module: {str(e)}")
            raise

    def load_module(self, module_name: str) -> Optional[ModuleInterface]:
        """Dynamically load module interface from discovered modules."""
        try:
            # Import module
            module_path = f"src.{module_name}.deployment"
            try:
                module = import_module(module_path)
                log.debug(f"Imported module from path: {module_path}")
            except ImportError as e:
                raise ModuleLoadError(
                    f"Failed to import {module_path}: {str(e)}"
                ) from e

            # Get module class
            class_name = f"{module_name.capitalize()}Module"
            if not hasattr(module, class_name):
                raise ModuleLoadError(
                    f"Module {module_name} missing {class_name} class"
                )

            log.debug(f"Found module class: {class_name}")

            # Instantiate module
            module_class = getattr(module, class_name)
            module_instance = module_class(self.init_config)
            log.debug(f"Instantiated module: {module_instance}")

            # Verify interface implementation
            if not isinstance(module_instance, ModuleInterface):
                raise ModuleLoadError(
                    f"Module {module_name} does not implement ModuleInterface"
                )

            log.info(f"Successfully loaded module: {module_name}")
            return module_instance

        except Exception as e:
            log.error(f"Failed to load module {module_name}: {str(e)}")
            raise
