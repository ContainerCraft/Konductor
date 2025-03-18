# src/core/module.py

"""Core module for the Infrastructure as Code framework."""

import pulumi
from typing import Dict, Any

from .config.config_manager import ConfigManager
from .logging.log_manager import LogManager
from .providers.provider_discovery import ProviderDiscovery
from .providers.provider_registry import ProviderRegistry


class CoreModule:
    """Orchestrates the core functionality of the IaC framework.

    The CoreModule is responsible for orchestrating the core functionality of the
    framework, including configuration management, provider discovery, logging
    system initialization, and metadata collection.

    This class serves as the main entry point for the core module functionality.
    """

    def __init__(self):
        """Initialize the Core Module."""
        # Initialize logging system
        self.log_manager = LogManager()
        self.logger = self.log_manager.get_logger("core")
        self.logger.info("Initializing Core Module")

        # Initialize configuration system
        self.config_manager = ConfigManager()

        # Initialize provider discovery and registry
        self.provider_discovery = ProviderDiscovery(self.log_manager)
        self.provider_registry = ProviderRegistry(self.log_manager)

        # Register discovered provider modules
        self._register_providers()

    def _register_providers(self) -> None:
        """Register provider modules with the provider registry."""
        self.logger.info("Registering provider modules")
        # Discover available provider modules
        provider_modules = self.provider_discovery.discover_provider_modules()
        self.logger.info(f"Discovered {len(provider_modules)} provider modules")

    def run(self) -> None:
        """Execute the core module workflow."""
        self.logger.info("Starting Core Module execution")

        # Generate stack outputs and metadata
        stack_outputs = self._generate_stack_outputs()

        # Output program completion status
        self.logger.info("Core Module execution completed successfully")

    def _generate_stack_outputs(self) -> Dict[str, Any]:
        """Generate stack outputs for the core module.

        Returns:
            Dict containing stack outputs.
        """
        outputs = {
            "status": "success",
            "core": {
                "version": "0.1.0",
                "name": "core-module"
            }
        }

        # Export the outputs to Pulumi
        for key, value in outputs.items():
            pulumi.export(key, value)

        return outputs
