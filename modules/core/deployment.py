# ./modules/core/deployment.py
import importlib
from pulumi import log
from typing import List, Dict, Optional

from modules.core.types import InitializationConfig
from modules.core.interfaces import ModuleDeploymentResult, ModuleInterface

class DeploymentManager:
    """Manages module deployment orchestration."""

    def __init__(self, init_config: InitializationConfig):
        self.init_config = init_config
        self.modules = {
            "aws": "modules.aws.deploy.AWSModule"
        }
        self.results: Dict[str, ModuleDeploymentResult] = {}

    def deploy_module(self, module_name: str) -> Optional[ModuleDeploymentResult]:
        try:
            # Load module
            module = self._load_module(module_name)

            # Get module configuration
            module_config = self.init_config.config.get_object(module_name)

            # Let module validate its own config
            validation_errors = module.validate_config(module_config)
            if validation_errors:
                raise ValueError(f"Configuration validation failed: {validation_errors}")

            # Let module perform pre-deployment checks
            pre_deploy_errors = module.pre_deploy_check()
            if pre_deploy_errors:
                raise ValueError(f"Pre-deployment checks failed: {pre_deploy_errors}")

            # Deploy
            result = module.deploy(module_config, self.init_config)

            # Let module validate deployment result
            post_deploy_errors = module.post_deploy_validation(result)
            if post_deploy_errors:
                raise ValueError(f"Post-deployment validation failed: {post_deploy_errors}")

            return result

        except Exception as e:
            log.error(f"Module deployment failed: {str(e)}")
            raise

    def deploy_modules(self, modules_to_deploy: List[str]) -> None:
        """
        Deploys the enabled modules in dependency order.

        Args:
            modules_to_deploy: A list of module names to deploy.
        """
        log.info(f"Deploying modules: {', '.join(modules_to_deploy)}")

        # Build dependency graph
        dependency_graph = {}
        for module_name in modules_to_deploy:
            try:
                module = self._load_module(module_name)
                dependencies = module.get_dependencies()
                dependency_graph[module_name] = dependencies
            except ImportError:
                log.warn(f"Could not load dependencies for module {module_name}")
                dependency_graph[module_name] = []

        # Sort modules by dependencies
        deployed = set()
        deployment_order = []

        def deploy_with_deps(module: str):
            if module in deployed:
                return
            for dep in dependency_graph.get(module, []):
                if dep in modules_to_deploy:
                    deploy_with_deps(dep)
            deployment_order.append(module)
            deployed.add(module)

        # Deploy modules in dependency order
        for module in modules_to_deploy:
            deploy_with_deps(module)

        # Actually deploy the modules
        for module_name in deployment_order:
            try:
                result = self.deploy_module(module_name)
                if result:
                    self.results[module_name] = result
            except Exception as e:
                log.error(f"Failed to deploy module {module_name}: {str(e)}")
                raise

    def _load_module(self, module_name: str) -> ModuleInterface:
        if module_name not in self.modules:
            raise ValueError(f"Unknown module: {module_name}")

        module_path = self.modules[module_name]
        module_parts = module_path.split(".")

        try:
            module = importlib.import_module(".".join(module_parts[:-1]))
            return getattr(module, module_parts[-1])()
        except (ImportError, AttributeError) as e:
            log.error(f"Failed to load module {module_name}: {str(e)}")
            raise
