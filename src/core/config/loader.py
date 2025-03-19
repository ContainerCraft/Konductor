# src/core/config/loader.py

"""Configuration loading utilities for the IaC framework.

This module contains tools for loading configurations from various sources
with proper precedence handling:
1. Default configurations (lowest priority)
2. Pulumi stack configuration (medium priority)
3. Environment variables for credentials only (highest priority)
"""

import os
import logging
import pulumi
from typing import Dict, Any, Optional

from .defaults import get_default_config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries with override taking precedence.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()

    for key, value in override.items():
        # If both values are dictionaries, merge them recursively
        if (
            key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            # Otherwise override the value
            result[key] = value

    return result


class ConfigLoader:
    """Configuration loader for the IaC framework.

    Responsible for loading configuration from multiple sources with
    proper precedence handling.
    """

    def __init__(self, pulumi_config: Optional[pulumi.Config] = None, 
                 logger: Optional[logging.Logger] = None):
        """Initialize the configuration loader.

        Args:
            pulumi_config: Optional Pulumi config instance.
            logger: Optional logger instance.
        """
        self.pulumi_config = pulumi_config or pulumi.Config()
        self.logger = logger or logging.getLogger("core.config.loader")

    def load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values.

        Returns:
            Dict containing default configuration.
        """
        self.logger.debug("Loading default configuration values")
        return get_default_config()

    def load_from_pulumi_stack(self) -> Dict[str, Any]:
        """Load configuration from Pulumi stack YAML.

        Returns:
            Dict containing configuration from Pulumi stack.
        """
        self.logger.debug("Loading configuration from Pulumi stack")
        stack_config: Dict[str, Any] = {}

        try:
            # Try to get the entire config as an object
            # This requires a "config" section in the Pulumi.<stack>.yaml
            all_config = self.pulumi_config.get_object("")

            if all_config is not None:
                stack_config = all_config
                self.logger.debug(f"Loaded {len(stack_config)} configuration sections from stack")
            else:
                # Fallback to loading individual top-level sections
                self.logger.debug("No root configuration object found, loading sections individually")
                for section in ["project", "logging", "aws", "azure", "kubernetes", "providers"]:
                    try:
                        section_config = self.pulumi_config.get_object(section)
                        if section_config is not None:
                            stack_config[section] = section_config
                            self.logger.debug(f"Loaded configuration section: {section}")
                    except Exception as section_err:
                        self.logger.debug(f"Error loading section {section}: {str(section_err)}")
        except Exception as e:
            self.logger.warning(f"Error loading stack configuration: {str(e)}")
            # Don't raise - we fall back to defaults

        return stack_config

    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from all sources with proper precedence.

        Returns:
            Dict containing merged configuration.
        """
        # Start with default configuration (lowest priority)
        config = self.load_defaults()

        # Load from Pulumi stack (overrides defaults)
        stack_config = self.load_from_pulumi_stack()
        config = deep_merge(config, stack_config)

        return config