# pulumi/core/deployment.py

"""
Deployment Management Module

This module manages the deployment orchestration of modules,
initializes Pulumi and Kubernetes providers, and handles module deployments.
"""

import os
import inspect
import importlib
from pydantic import BaseModel
from typing import Dict, Any, List, Type, Callable

import pulumi
import pulumi_kubernetes as k8s
from pulumi import log
from pulumi_kubernetes import Provider

from .config import get_module_config, load_default_versions
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
from .types import ComplianceConfig


def initialize_pulumi() -> Dict[str, Any]:
    """
    Initializes Pulumi configuration, Kubernetes provider, and global resources.

    Returns:
        Dict[str, Any]: A dictionary containing initialized components.
    """
    config = pulumi.Config()
    stack_name = pulumi.get_stack()
    project_name = pulumi.get_project()

    try:
        # Load global default versions and initialize variables from configuration.
        default_versions = load_default_versions(config)
        versions: Dict[str, str] = {}

        # Initialize empty global configuration and dependency list variables.
        configurations: Dict[str, Dict[str, Any]] = {}
        global_depends_on: List[pulumi.Resource] = []

        # Initialize the Kubernetes provider.
        kubernetes_config = config.get_object("kubernetes") or {}
        kubernetes_context = kubernetes_config.get("context")

        kubeconfig = kubernetes_config.get("kubeconfig") or os.getenv("KUBECONFIG")

        # Initialize the Kubernetes provider.
        k8s_provider = Provider(
            "k8sProvider",
            kubeconfig=kubeconfig,
            context=kubernetes_context,
        )

        k8s_provider_secret = pulumi.Output.secret(k8s_provider)
        pulumi.export("k8s_provider", k8s_provider_secret)

        log.info(f"Kubeconfig: {kubeconfig}")
        log.info(f"Kubernetes context: {kubernetes_context}")

        # Collect and store git information in the global configuration.
        git_info = collect_git_info()
        configurations["source_repository"] = {
            "remote": git_info["remote"],
            "branch": git_info["branch"],
            "commit": git_info["commit"],
        }

        # Retrieve compliance metadata from pulumi configuration.
        compliance_config_dict = config.get_object("compliance") or {}
        compliance_config = ComplianceConfig.merge(compliance_config_dict)
        pulumi.log.info(f"Compliance Config: {compliance_config}")

        # Generate global tags, labels, and annotations.
        compliance_labels = generate_compliance_labels(compliance_config)
        compliance_annotations = generate_compliance_annotations(compliance_config)

        git_labels = generate_git_labels(git_info)
        git_annotations = generate_git_annotations(git_info)
        global_labels = {**compliance_labels, **git_labels}
        global_annotations = {**compliance_annotations, **git_annotations}

        set_global_labels(global_labels)
        set_global_annotations(global_annotations)
        generate_global_transformations(global_labels, global_annotations)

        return {
            "config": config,
            "stack_name": stack_name,
            "project_name": project_name,
            "default_versions": default_versions,
            "versions": versions,
            "configurations": configurations,
            "global_depends_on": global_depends_on,
            "k8s_provider": k8s_provider,
            "git_info": git_info,
            "compliance_config": compliance_config,
            "global_labels": global_labels,
            "global_annotations": global_annotations,
        }
    except Exception as e:
        log.error(f"Initialization error: {str(e)}")
        raise


def deploy_module(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any],
    global_depends_on: List[pulumi.Resource],
    k8s_provider: k8s.Provider,
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]],
    compliance_config: ComplianceConfig,  # Include this parameter
) -> None:
    """
    Helper function to deploy a module based on configuration.

    Args:
        module_name (str): Name of the module.
        config (pulumi.Config): Pulumi configuration object.
        default_versions (Dict[str, Any]): Default versions for modules.
        global_depends_on (List[pulumi.Resource]): Global dependencies.
        k8s_provider (k8s.Provider): Kubernetes provider.
        versions (Dict[str, str]): Dictionary to store versions of deployed modules.
        configurations (Dict[str, Dict[str, Any]]): Dictionary to store configurations of deployed modules.
        compliance_config (ComplianceConfig): Compliance configuration for the stack.
    """
    if not isinstance(module_name, str):
        raise TypeError("module_name must be a string")
    if not isinstance(config, pulumi.Config):
        raise TypeError("config must be an instance of pulumi.Config")
    if not isinstance(default_versions, dict):
        raise TypeError("default_versions must be a dictionary")
    if not isinstance(global_depends_on, list):
        raise TypeError("global_depends_on must be a list")
    if not isinstance(k8s_provider, k8s.Provider):
        raise TypeError(
            "k8s_provider must be an instance of pulumi_kubernetes.Provider"
        )
    if not isinstance(versions, dict):
        raise TypeError("versions must be a dictionary")
    if not isinstance(configurations, dict):
        raise TypeError("configurations must be a dictionary")

    # Retrieve module configuration and enabled status.
    module_config_dict, module_enabled = get_module_config(
        module_name, config, default_versions
    )

    if module_enabled:
        ModuleConfigClass = discover_config_class(module_name)
        deploy_func = discover_deploy_function(module_name)

        config_obj = ModuleConfigClass.merge(module_config_dict)

        deploy_func_args = inspect.signature(deploy_func).parameters.keys()
        config_arg_name = list(deploy_func_args)[0]

        deploy_kwargs = {
            config_arg_name: config_obj,
            "global_depends_on": global_depends_on,
        }

        if module_name != "aws":
            deploy_kwargs["k8s_provider"] = k8s_provider

        try:
            result = deploy_func(**deploy_kwargs)

            if isinstance(result, tuple) and len(result) == 3:
                version, release, module_aux_meta = result
            elif isinstance(result, tuple) and len(result) == 2:
                version, release = result
                module_aux_meta = None
            else:
                raise ValueError(
                    f"Unexpected return value structure from {module_name} deploy function"
                )

            versions[module_name] = version
            configurations[module_name] = {"enabled": module_enabled}

            if module_aux_meta:
                # Include module outputs into configurations[module_name]
                configurations[module_name].update(module_aux_meta)

            global_depends_on.append(release)

        except Exception as e:
            log.error(f"Deployment failed for module {module_name}: {str(e)}")
            raise
    else:
        log.info(f"Module {module_name} is not enabled.")


def discover_config_class(module_name: str) -> Type:
    """
    Discovers and returns the configuration class from the module's types.py.
    Supports both Pydantic BaseModel and dataclasses.

    Args:
        module_name (str): The name of the module.

    Returns:
        Type: The configuration class, either a Pydantic BaseModel subclass or a dataclass.

    Raises:
        ValueError: If no suitable configuration class is found.
    """
    types_module = importlib.import_module(f"modules.{module_name}.types")
    config_class: Optional[Type] = None

    for name, obj in inspect.getmembers(types_module):
        if inspect.isclass(obj):
            if issubclass(obj, BaseModel) and obj is not BaseModel:
                return obj
            elif hasattr(obj, "__dataclass_fields__"):
                config_class = obj

    if config_class:
        return config_class

    raise ValueError(f"No configuration class found in modules.{module_name}.types")


def discover_deploy_function(module_name: str) -> Callable:
    """
    Discovers and returns the deploy function from the module's deploy.py.

    Args:
        module_name (str): The name of the module.

    Returns:
        Callable: The deploy function.
    """
    deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
    function_name = f"deploy_{module_name}_module"
    deploy_function = getattr(deploy_module, function_name, None)
    if not deploy_function:
        raise ValueError(
            f"No deploy function named '{function_name}' found in modules.{module_name}.deploy"
        )
    return deploy_function


def deploy_modules(
    modules: List[str],
    config: pulumi.Config,
    default_versions: Dict[str, Any],
    global_depends_on: List[pulumi.Resource],
    k8s_provider: Provider,
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]],
    compliance_config: ComplianceConfig,
) -> None:
    """
    Iterates over a list of modules and deploys each configured and enabled module.

    Args:
        modules (List[str]): List of module names to deploy.
        config (pulumi.Config): Pulumi configuration object.
        default_versions (Dict[str, Any]): Default versions for modules.
        global_depends_on (List[pulumi.Resource]): Global dependencies.
        k8s_provider (k8s.Provider): Kubernetes provider.
        versions (Dict[str, str]): Dictionary to store versions of deployed modules.
        configurations (Dict[str, Dict[str, Any]]): Dictionary to store configurations of deployed modules.
    """
    for module_name in modules:
        log.info(f"Deploying module: {module_name}")
        deploy_module(
            module_name=module_name,
            config=config,
            default_versions=default_versions,
            global_depends_on=global_depends_on,
            k8s_provider=k8s_provider,
            versions=versions,
            configurations=configurations,
            compliance_config=compliance_config,
        )
