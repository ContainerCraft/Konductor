# ./modules/core/config.py
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
import pulumi
import requests

from pulumi import log
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, List
from pydantic import ValidationError
from urllib.parse import urlparse

from .types import (
    InitializationConfig,
    ModuleDefaults,
    ModuleBase,
    StackOutputs,
)
from .compliance_types import ComplianceConfig


# Configuration Constants
DEFAULT_VERSIONS_URL_TEMPLATE = "https://raw.githubusercontent.com/ContainerCraft/Kargo/newfactor/modules/"

CACHE_DIR = Path("/tmp/konductor")
VERSION_CACHE_FILE = CACHE_DIR / "default_versions.json"

# Default module configuration
DEFAULT_MODULE_CONFIG: Dict[str, ModuleDefaults] = {
    "cert_manager": {"enabled": False, "version": None, "config": {}},
    "kubevirt": {"enabled": False, "version": None, "config": {}},
    "multus": {"enabled": False, "version": None, "config": {}},
    "hostpath_provisioner": {"enabled": False, "version": None, "config": {}},
    "containerized_data_importer": {"enabled": False, "version": None, "config": {}},
    "prometheus": {"enabled": False, "version": None, "config": {}},
}


def ensure_cache_dir() -> None:
    """Ensures the cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def coerce_to_bool(value: Any) -> bool:
    """
    Coerces a value to a boolean.

    Args:
        value: The value to coerce.

    Returns:
        bool: The coerced boolean value.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def get_module_config(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, str],
    namespace: Optional[str] = None,
) -> Tuple[Dict[str, Any], bool]:
    """
    Retrieves and prepares the configuration for a module.

    Args:
        module_name: The name of the module to configure
        config: The Pulumi configuration object
        default_versions: A dictionary of default versions for modules
        namespace: Optional namespace for module configuration

    Returns:
        A tuple containing:
            - Module's configuration dictionary
            - Boolean indicating if the module is enabled

    Raises:
        ValueError: If module configuration is invalid
    """
    try:
        module_defaults = DEFAULT_MODULE_CONFIG.get(module_name, ModuleDefaults(enabled=False, version=None, config={}))

        # Get module configuration from Pulumi config
        module_config: Dict[str, Any] = config.get_object(module_name) or {}

        # Determine if module is enabled
        enabled = coerce_to_bool(module_config.get("enabled", module_defaults["enabled"]))

        # Get module version
        version = module_config.get("version", default_versions.get(module_name))

        if version:
            module_config["version"] = version

        return module_config, enabled

    except Exception as e:
        log.error(f"Error configuring module {module_name}: {str(e)}")
        raise


def validate_version_format(version: str) -> bool:
    """
    Validates version string format.

    Args:
        version: Version string to validate

    Returns:
        bool: True if valid format
    """
    try:
        # Basic semver validation
        parts = version.split(".")
        return len(parts) >= 2 and all(part.isdigit() for part in parts)
    except Exception:
        return False


def load_versions_from_file(file_path: Path) -> Dict[str, Any]:
    """
    Loads version information from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dict[str, Any]: Version information dictionary.
    """
    try:
        if file_path.exists():
            with file_path.open("r") as f:
                versions = json.load(f)
                # Validate version formats
                for module, version in versions.items():
                    if version and not validate_version_format(str(version)):
                        log.warn(f"Invalid version format for {module}: {version}")
                log.info(f"Loaded versions from {file_path}")
                return versions
    except (json.JSONDecodeError, OSError) as e:
        log.warn(f"Error loading versions from {file_path}: {str(e)}")
    return {}


def load_versions_from_url(url: str) -> Dict[str, Any]:
    """
    Loads version information from a URL.

    Args:
        url: URL to fetch versions from.

    Returns:
        Dict[str, Any]: Version information dictionary.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        versions = response.json()
        log.info(f"Loaded versions from {url}")
        return versions
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.warn(f"Error loading versions from {url}: {str(e)}")
    return {}


def load_default_versions(config: pulumi.Config, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Loads the default versions for modules based on configuration settings.

    This function attempts to load version information from multiple sources:
    1. User-specified source via config
    2. Stack-specific versions file
    3. Local default versions file
    4. Remote versions based on channel

    Args:
        config: The Pulumi configuration object.
        force_refresh: Whether to force refresh the versions cache.

    Returns:
        Dict[str, Any]: Default versions for modules.

    Raises:
        Exception: If versions cannot be loaded from any source.
    """
    ensure_cache_dir()

    if not force_refresh and VERSION_CACHE_FILE.exists():
        if versions := load_versions_from_file(VERSION_CACHE_FILE):
            return versions

    stack_name = pulumi.get_stack()
    default_versions_source = config.get("default_versions.source")
    versions_channel = config.get("versions.channel") or "stable"
    versions_stack_name = coerce_to_bool(config.get("versions.stack_name")) or False

    # Try loading from specified source
    if default_versions_source:
        if default_versions_source.startswith(("http://", "https://")):
            versions = load_versions_from_url(default_versions_source)
        else:
            versions = load_versions_from_file(Path(default_versions_source))

        if versions:
            _cache_versions(versions)
            return versions
        raise Exception(f"Failed to load versions from {default_versions_source}")

    # Try stack-specific versions
    if versions_stack_name:
        stack_versions_path = Path(__file__).parent.parent / "versions" / f"{stack_name}.json"
        if versions := load_versions_from_file(stack_versions_path):
            _cache_versions(versions)
            return versions

    # Try local default versions
    default_versions_path = Path(__file__).parent.parent / "default_versions.json"
    if versions := load_versions_from_file(default_versions_path):
        _cache_versions(versions)
        return versions

    # Try remote versions
    versions_url = f"{DEFAULT_VERSIONS_URL_TEMPLATE}{versions_channel}_versions.json"
    if versions := load_versions_from_url(versions_url):
        _cache_versions(versions)
        return versions

    raise Exception("Cannot proceed without default versions")


def _cache_versions(versions: Dict[str, Any]) -> None:
    """
    Caches version information to file.

    Args:
        versions: Version information to cache.
    """
    try:
        with VERSION_CACHE_FILE.open("w") as f:
            json.dump(versions, f)
    except OSError as e:
        log.warn(f"Failed to cache versions: {str(e)}")


def export_results(
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]],
    compliance: ComplianceConfig,
) -> None:
    """
    Exports deployment results including versions, configurations, and compliance information.

    Args:
        versions: Versions of deployed modules.
        configurations: Configurations of deployed modules.
        compliance: Compliance configuration.
    """
    try:
        # Convert compliance to dictionary if it's a Pydantic model
        compliance_dict = compliance.dict() if isinstance(compliance, ComplianceConfig) else compliance

        # Export results
        pulumi.export("versions", versions)
        pulumi.export("configuration", configurations)
        pulumi.export("compliance", compliance_dict)

    except Exception as e:
        log.error(f"Failed to export results: {str(e)}")
        raise


def validate_url(url: str) -> bool:
    """
    Validates URL format.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid format
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_module_config(
    module_name: str,
    config: Dict[str, Any],
    module_class: Optional[type[ModuleBase]] = None,
) -> None:
    """
    Validates module configuration against its schema.

    Args:
        module_name: Name of the module.
        config: Module configuration to validate.
        module_class: Optional module configuration class.

    Raises:
        ValueError: If configuration is invalid.
    """
    try:
        # Validate basic structure
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Check required fields
        required_fields = {"enabled", "version"}
        missing_fields = required_fields - set(config.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate with module class if provided
        if module_class:
            module_class(**config)

        # Validate version if present
        if version := config.get("version"):
            if not validate_version_format(str(version)):
                raise ValueError(f"Invalid version format: {version}")

    except ValidationError as e:
        log.error(f"Invalid configuration for module {module_name}: {str(e)}")
        raise ValueError(f"Invalid configuration for module {module_name}: {str(e)}")
    except Exception as e:
        log.error(f"Configuration validation failed for {module_name}: {str(e)}")
        raise


def merge_configurations(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two configurations with override taking precedence.

    Args:
        base_config: Base configuration
        override_config: Override configuration

    Returns:
        Dict[str, Any]: Merged configuration
    """
    result = base_config.copy()
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configurations(result[key], value)
        else:
            result[key] = value
    return result


def initialize_config(stack_config: Dict[str, Any]) -> InitializationConfig:
    """
    Initializes core configuration from stack configuration.

    Args:
        stack_config: Stack configuration dictionary.

    Returns:
        InitializationConfig: Initialized configuration object.

    Raises:
        ValueError: If configuration is invalid.
    """
    try:
        # Validate stack config structure
        if not isinstance(stack_config, dict):
            raise ValueError("Stack configuration must be a dictionary")

        # Ensure required fields
        required_fields = {"project_name", "stack_name"}
        missing_fields = required_fields - set(stack_config.keys())
        if missing_fields:
            raise ValueError(f"Missing required stack configuration fields: {missing_fields}")

        # Initialize with validated config
        config = InitializationConfig(**stack_config)

        # Validate provider configurations
        if config.k8s_provider:
            # Add provider-specific validation here
            pass

        return config

    except ValidationError as e:
        log.error(f"Invalid initialization configuration: {str(e)}")
        raise ValueError(f"Invalid initialization configuration: {str(e)}")
    except Exception as e:
        log.error(f"Configuration initialization failed: {str(e)}")
        raise


def get_enabled_modules(config: pulumi.Config) -> List[str]:
    """
    Returns a list of module names that are enabled in the configuration.

    Args:
        config: The Pulumi configuration object.

    Returns:
        A list of enabled module names.
    """
    enabled_modules = []
    for module_name, module_defaults in DEFAULT_MODULE_CONFIG.items():
        # Get the configuration value with proper error handling
        config_key = f"konductor:{module_name}:enabled"
        is_enabled = config.get_bool(config_key)

        # Use default if no config value found
        if is_enabled is None:
            is_enabled = module_defaults["enabled"]

        log.info(f"Module {module_name} enabled status: {is_enabled}")
        if is_enabled:
            enabled_modules.append(module_name)

    return enabled_modules


def load_default_versions(config: pulumi.Config) -> Dict[str, str]:
    """
    Loads the default versions for modules.

    Args:
        config: The Pulumi configuration object.

    Returns:
        Dict[str, str]: A dictionary of module names to default versions.
    """
    # Implement logic to load default versions, possibly from a file or remote source
    # For simplicity, return an empty dictionary here
    return {}


def get_stack_outputs(init_config: InitializationConfig) -> StackOutputs:
    """
    Generate standardized stack outputs.

    Args:
        init_config: The initialization configuration object

    Returns:
        StackOutputs: Dictionary containing all stack outputs
    """
    try:
        # Get compliance data
        compliance_data = init_config.compliance_config or {}

        # Get configuration subset
        config_data = {
            "stack_name": init_config.stack_name,
            "project_name": init_config.project_name,
            "versions": init_config.versions,
            "configurations": init_config.configurations,
        }

        # Get Kubernetes component versions
        k8s_versions = {
            name: config.get("version", "unknown")
            for name, config in init_config.configurations.items()
            if name in ["cert_manager", "kubevirt", "multus", "pulumi_operator", "crossplane"]
        }

        # Construct the StackOutputs TypedDict
        stack_outputs: StackOutputs = {
            "compliance": compliance_data,
            "config": config_data,
            "k8s_app_versions": k8s_versions,
        }

        return stack_outputs

    except Exception as e:
        log.error(f"Failed to generate stack outputs: {str(e)}")
        raise


class ConfigManager:
    def __init__(self):
        self.pulumi_config = pulumi.Config()
        self.global_config = self.load_global_config()
        self.module_configs = self.load_module_configs()

    def load_global_config(self):
        # Load global configuration
        return self.pulumi_config.get_object("global") or {}

    def load_module_configs(self):
        # Load configurations for each enabled module
        module_configs = {}
        enabled_modules = self.get_enabled_modules()
        for module_name in enabled_modules:
            module_key = f"module:{module_name}"
            module_config = self.pulumi_config.get_object(module_key) or {}
            module_configs[module_name] = module_config
        return module_configs

    def get_enabled_modules(self) -> List[str]:
        """Get list of enabled modules from config."""
        enabled_modules = []

        # Look for modules directory
        modules_dir = Path(__file__).parent.parent

        # Scan for module directories
        for module_dir in modules_dir.iterdir():
            if not module_dir.is_dir() or module_dir.name == "core":
                continue

            module_name = module_dir.name
            try:
                # Import module's config
                module_config = self.get_module_config(module_name)

                # Check if module is enabled
                is_enabled = module_config.get("enabled", False)

                if is_enabled:
                    log.info(f"{module_name} module is enabled in configuration")
                    enabled_modules.append(module_name)
                else:
                    log.debug(f"{module_name} module is not enabled")

            except Exception as e:
                log.warn(f"Error checking module {module_name}: {str(e)}")
                continue

        return enabled_modules

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        try:
            # Try to get module config from Pulumi stack config
            stack_config = self.pulumi_config.get_object(module_name) or {}

            # Try to import module's default config
            try:
                module_config = __import__(f"modules.{module_name}.config", fromlist=["DEFAULT_MODULE_CONFIG"])
                default_config = getattr(module_config, "DEFAULT_MODULE_CONFIG", {})
            except (ImportError, AttributeError):
                default_config = {}

            # Merge configs with stack config taking precedence
            return {**default_config, **stack_config}

        except Exception as e:
            log.warn(f"Error loading config for module {module_name}: {str(e)}")
            return {}
