# pulumi/core/deployment.py

"""
Deployment Management Module

This module manages the deployment orchestration of modules,
initializes Pulumi and Kubernetes providers, and handles module deployments.

Key Functions:
- initialize_pulumi: Initializes Pulumi configuration and providers
- deploy_modules: Orchestrates module deployments
- deploy_module: Handles individual module deployment
"""

import os
import inspect
import importlib
from typing import Dict, Any, List, Type, Callable, Optional, cast
from pydantic import ValidationError

import pulumi
import pulumi_kubernetes as k8s
from pulumi import log
from pulumi_kubernetes import Provider

from .config import (
    get_module_config,
    load_default_versions,
    initialize_config,
    validate_module_config
)
from .metadata import (
    collect_git_info,
    generate_git_labels,
    generate_git_annotations,
    set_global_labels,
    set_global_annotations,
    generate_compliance_labels,
    generate_compliance_annotations,
)
from .utils import generate_global_transformations
from .types import (
    ComplianceConfig,
    InitializationConfig,
    ModuleDeploymentResult
)
from .resource_helpers import create_namespace

class DeploymentManager:
    """
    Manages module deployment and lifecycle.

    Handles initialization, deployment orchestration, and cleanup of modules.
    Ensures proper resource management and error handling.
    """

    def __init__(self, init_config: InitializationConfig):
        """
        Initialize deployment manager.

        Args:
            init_config: Initialization configuration
        """
        self.init_config = init_config
        self.deployed_modules: Dict[str, ModuleDeploymentResult] = {}
        self._setup_global_metadata()

    def _setup_global_metadata(self) -> None:
        """Sets up global metadata for all resources."""
        try:
            # Generate metadata
            git_info = collect_git_info()
            git_labels = generate_git_labels(git_info)
            git_annotations = generate_git_annotations(git_info)

            compliance_labels = generate_compliance_labels(self.init_config.compliance_config)
            compliance_annotations = generate_compliance_annotations(
                self.init_config.compliance_config
            )

            # Combine metadata
            global_labels = {**compliance_labels, **git_labels}
            global_annotations = {**compliance_annotations, **git_annotations}

            # Set global metadata
            set_global_labels(global_labels)
            set_global_annotations(global_annotations)

            # Register global transformations
            generate_global_transformations(global_labels, global_annotations)

        except Exception as e:
            log.error(f"Failed to setup global metadata: {str(e)}")
            raise

    def discover_module_config(self, module_name: str) -> Type:
        """
        Discovers and returns the configuration class from the module's types.py.

        Args:
            module_name: The name of the module

        Returns:
            Type: The configuration class

        Raises:
            ImportError: If module cannot be imported
            ValueError: If no suitable configuration class is found
        """
        try:
            types_module = importlib.import_module(f"modules.{module_name}.types")

            for name, obj in inspect.getmembers(types_module):
                if inspect.isclass(obj):
                    if hasattr(obj, "Config"):  # Pydantic model
                        return obj
                    elif hasattr(obj, "__dataclass_fields__"):  # Dataclass
                        return obj

            raise ValueError(f"No configuration class found in modules.{module_name}.types")

        except ImportError as e:
            log.error(f"Failed to import module {module_name}: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error discovering module config: {str(e)}")
            raise

    def discover_deploy_function(self, module_name: str) -> Callable:
        """
        Discovers and returns the deploy function from the module's deploy.py.

        Args:
            module_name: The name of the module

        Returns:
            Callable: The deploy function

        Raises:
            ImportError: If module cannot be imported
            ValueError: If deploy function is not found
        """
        try:
            deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
            function_name = f"deploy_{module_name}_module"

            if deploy_func := getattr(deploy_module, function_name, None):
                return deploy_func

            raise ValueError(
                f"No deploy function named '{function_name}' found in modules.{module_name}.deploy"
            )

        except ImportError as e:
            log.error(f"Failed to import module {module_name}: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error discovering deploy function: {str(e)}")
            raise

    def deploy_module(self, module_name: str) -> ModuleDeploymentResult:
        """
        Deploys a single module with proper error handling.

        Args:
            module_name: Name of the module to deploy

        Returns:
            ModuleDeploymentResult: Result of the deployment

        Raises:
            ValueError: If module configuration is invalid
        """
        try:
            # Get module configuration
            module_config, module_enabled = get_module_config(
                module_name,
                self.init_config.config,
                self.init_config.default_versions
            )

            if not module_enabled:
                log.info(f"Module {module_name} is not enabled, skipping deployment")
                return ModuleDeploymentResult(
                    success=True,
                    version="",
                    resources=[],
                    metadata={"enabled": False}
                )

            # Import module dynamically
            module = importlib.import_module(f"modules.{module_name}")
            deploy_func = getattr(module, f"deploy_{module_name}_module")

            # Deploy with proper error handling
            result = deploy_func(
                module_config,
                self.init_config.global_depends_on
            )

            # Track deployment
            self.deployed_modules[module_name] = result
            return result

        except Exception as e:
            log.error(f"Failed to deploy module {module_name}: {str(e)}")
            return ModuleDeploymentResult(
                success=False,
                version="",
                resources=[],
                errors=[str(e)]
            )

def initialize_pulumi() -> InitializationConfig:
    """
    Initializes Pulumi configuration, Kubernetes provider, and global resources.

    Returns:
        InitializationConfig: Initialized configuration object

    Raises:
        Exception: If initialization fails
    """
    try:
        # Initialize basic configuration
        config = pulumi.Config()
        stack_name = pulumi.get_stack()
        project_name = pulumi.get_project()

        # Load default versions
        default_versions = load_default_versions(config)
        versions: Dict[str, str] = {}
        configurations: Dict[str, Dict[str, Any]] = {}
        global_depends_on: List[pulumi.Resource] = []

        # Initialize Kubernetes provider
        kubernetes_config = config.get_object("kubernetes") or {}
        kubernetes_context = kubernetes_config.get("context")
        kubeconfig = kubernetes_config.get("kubeconfig") or os.getenv("KUBECONFIG")

        k8s_provider = Provider(
            "k8s_provider",
            kubeconfig=kubeconfig,
            context=kubernetes_context,
        )

        # Get compliance configuration
        compliance_config_dict = config.get_object("compliance") or {}
        compliance_config = ComplianceConfig.merge(compliance_config_dict)

        # Initialize configuration object
        init_config = initialize_config({
            "config": config,
            "stack_name": stack_name,
            "project_name": project_name,
            "default_versions": default_versions,
            "versions": versions,
            "configurations": configurations,
            "global_depends_on": global_depends_on,
            "k8s_provider": k8s_provider,
            "git_info": collect_git_info(),
            "compliance_config": compliance_config
        })

        return init_config

    except Exception as e:
        log.error(f"Initialization failed: {str(e)}")
        raise

def deploy_modules(
    modules: List[str],
    init_config: InitializationConfig
) -> None:
    """
    Deploys a list of modules in order.

    Args:
        modules: List of module names to deploy
        init_config: Initialization configuration

    Raises:
        Exception: If deployment fails
    """
    try:
        deployment_manager = DeploymentManager(init_config)

        for module_name in modules:
            log.info(f"Deploying module: {module_name}")

            result = deployment_manager.deploy_module(module_name)

            if not result.success:
                log.error(
                    f"Failed to deploy module {module_name}: {', '.join(result.errors)}"
                )
                continue

            # Update versions and configurations
            if result.version:
                init_config.update_versions(module_name, result.version)

            init_config.configurations[module_name] = {
                "enabled": True,
                "version": result.version,
                **result.metadata
            }

    except Exception as e:
        log.error(f"Module deployment failed: {str(e)}")
        raise
