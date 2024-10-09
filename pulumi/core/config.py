# pulumi/core/config.py

"""
Configuration Management Module

This module handles the retrieval and preparation of configurations for different modules
within the Pulumi IaC program. It centralizes configuration logic to promote reuse
and maintainability.

Key Functions:
- get_module_config: Retrieves and prepares module configuration.
- load_default_versions: Loads default versions for modules.
- export_results: Exports global deployment stack metadata.

Includes proper data type handling to ensure configurations are correctly parsed.
"""

import json
import os
import pulumi
import requests
from typing import Any, Dict, Tuple, Optional
from .types import ComplianceConfig

# Default versions URL template
DEFAULT_VERSIONS_URL_TEMPLATE = 'https://raw.githubusercontent.com/ContainerCraft/Kargo/rerefactor/pulumi/'

# Module enabled defaults: Setting a module to True enables the module by default
DEFAULT_ENABLED_CONFIG = {
    "aws": False,
    "cert_manager": True,
    "kubevirt": True,
    "multus": True,
    "hostpath_provisioner": True,
    "containerized_data_importer": True,
    "prometheus": True,
}

def coerce_to_bool(value: Any) -> bool:
    """
    Coerces a value to a boolean.

    Args:
        value (Any): The value to coerce.

    Returns:
        bool: The coerced boolean value.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == 'true'
    return bool(value)

def get_module_config(
        module_name: str,
        config: pulumi.Config,
        default_versions: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], bool]:
    """
    Retrieves and prepares the configuration for a module.

    Args:
        module_name (str): The name of the module to configure.
        config (pulumi.Config): The Pulumi configuration object.
        default_versions (Dict[str, Any]): A dictionary of default versions for modules.

    Returns:
        Tuple[Dict[str, Any], bool]: A tuple containing the module's configuration dictionary
                                     and a boolean indicating if the module is enabled.
    """

    module_config = config.get_object(module_name) or {}

    # Retrieve enabled status from configuration or defaults to defined default setting
    enabled_value = module_config.pop('enabled', DEFAULT_ENABLED_CONFIG.get(module_name, False))
    module_enabled = coerce_to_bool(enabled_value)

    # Include 'compliance' config into 'module_config' for AWS module
    if module_name == 'aws':
        compliance_config_dict = config.get_object('compliance') or {}
        module_config['compliance'] = compliance_config_dict

    # Only set the version if it is *not* the aws module
    if module_name != "aws":
        module_config['version'] = module_config.get('version', default_versions.get(module_name))

    return module_config, module_enabled

def load_default_versions(config: pulumi.Config, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Loads the default versions for modules based on the specified configuration settings.

    This function attempts to load version information from multiple sources in order of precedence:
    1. User-specified source via Pulumi config (`default_versions.source`).
    2. Stack-specific versions file (`./versions/$STACK_NAME.json`) if `versions.stack_name` is set to true.
    3. Local default versions file (`./default_versions.json`).
    4. Remote versions based on the specified channel (`versions.channel`).

    Args:
        config (pulumi.Config): The Pulumi configuration object.
        force_refresh (bool): Whether to force refresh the versions cache.

    Returns:
        Dict[str, Any]: A dictionary containing the default versions for modules.

    Raises:
        Exception: If default versions cannot be loaded from any source.
    """
    cache_file = '/tmp/default_versions.json'
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                return json.load(f)
        except Exception as e:
            pulumi.log.warn(f"Error reading cache file: {e}")

    stack_name = pulumi.get_stack()
    default_versions_source = config.get('default_versions.source')
    versions_channel = config.get('versions.channel') or 'stable'
    versions_stack_name = coerce_to_bool(config.get('versions.stack_name')) or False
    default_versions = {}

    # Function to try loading default versions from file
    def load_versions_from_file(file_path: str) -> dict:
        try:
            with open(file_path, 'r') as f:
                versions = json.load(f)
                pulumi.log.info(f"Loaded default versions from file: {file_path}")
                return versions
        except (FileNotFoundError, json.JSONDecodeError) as e:
            pulumi.log.warn(f"Error loading versions from file {file_path}: {e}")
            return {}

    def load_versions_from_url(url: str) -> dict:
        try:
            response = requests.get(url)
            response.raise_for_status()
            versions = response.json()
            pulumi.log.info(f"Loaded default versions from URL: {url}")
            return versions
        except (requests.RequestException, json.JSONDecodeError) as e:
            pulumi.log.warn(f"Error loading versions from URL {url}: {e}")
            return {}

    if default_versions_source:
        if default_versions_source.startswith(('http://', 'https://')):
            default_versions = load_versions_from_url(default_versions_source)
        else:
            default_versions = load_versions_from_file(default_versions_source)

        if not default_versions:
            raise Exception(f"Failed to load default versions from specified source: {default_versions_source}")

    else:
        if versions_stack_name:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            stack_versions_path = os.path.join(current_dir, '..', 'versions', f'{stack_name}.json')
            default_versions = load_versions_from_file(stack_versions_path)

        if not default_versions:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_versions_path = os.path.join(current_dir, '..', 'default_versions.json')
            default_versions = load_versions_from_file(default_versions_path)

        if not default_versions:
            versions_url = f'{DEFAULT_VERSIONS_URL_TEMPLATE}{versions_channel}_versions.json'
            default_versions = load_versions_from_url(versions_url)

        if not default_versions:
            raise Exception("Cannot proceed without default versions.")

    with open(cache_file, 'w') as f:
        json.dump(default_versions, f)

    return default_versions

def export_results(
        versions: Dict[str, str],
        configurations: Dict[str, Dict[str, Any]],
        compliance: Any
    ):
    """
    Exports the results of the deployment processes including versions, configurations, and compliance information.

    Args:
        versions (Dict[str, str]): A dictionary containing the versions of the deployed modules.
        configurations (Dict[str, Dict[str, Any]]): A dictionary containing the configurations of the deployed modules.
        compliance (Any): The compliance configuration, can be ComplianceConfig or a dictionary.
    """
    # Convert compliance to a dictionary if it's a Pydantic model
    if hasattr(compliance, 'dict'):
        compliance_dict = compliance.dict()
    else:
        compliance_dict = compliance

    pulumi.export("versions", versions)
    pulumi.export("configuration", configurations)
    pulumi.export("compliance", compliance_dict)
