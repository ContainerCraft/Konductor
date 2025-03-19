# src/core/module.py

"""Core module implementation for the IaC framework."""

import os
import pulumi
from typing import Dict, List, Any

from .config.config_manager import ConfigManager
from .logging.log_manager import LogManager
from .providers.provider_registry import ProviderRegistry
from .providers.provider_discovery import ProviderDiscovery


class CoreModule:
    """Main Core Module implementation.

    This class orchestrates the core functionality of the IaC framework, including:
    - Configuration management
    - Provider discovery and registry
    - Logging system initialization
    - Metadata collection and management
    - Git integration
    - Deployment orchestration

    The core module serves as the central coordination point for all provider
    modules, handling configuration propagation, dependency management, and
    resource tracking.
    """

    def __init__(self):
        """Initialize the Core Module."""
        # First initialize basic logging with default settings
        # We'll update this after loading config
        self._init_basic_logging()

        # Next initialize configuration
        self._init_config()

        # Now update logging with config settings
        self._update_logging()

        # Initialize provider registry and discovery
        self.provider_registry = ProviderRegistry(self.config_manager, self.log_manager)
        self.provider_discovery = ProviderDiscovery(self.log_manager)
        self.logger.info("Provider registry and discovery initialized")

        # Initialize Git metadata collector
        self.git_metadata = {}
        self.logger.info("Core Module initialized")

    def _init_basic_logging(self) -> None:
        """Initialize basic logging with default settings."""
        # Use environment variable or default to info
        log_level = os.environ.get("PULUMI_LOG_LEVEL", "info").lower()

        self.log_manager = LogManager(log_level=log_level)
        self.logger = self.log_manager.get_logger("core")
        self.logger.info("Basic logging initialized")

    def _init_config(self) -> None:
        """Initialize the configuration system."""
        # Initialize ConfigManager
        self.config_manager = ConfigManager()
        self.logger.info("Configuration system initialized")

    def _update_logging(self) -> None:
        """Update the logging system with configuration settings."""
        # First check environment variable (highest priority for credentials/debugging)
        log_level = os.environ.get("PULUMI_LOG_LEVEL", "").lower()

        # If not set in environment, get from config
        if not log_level:
            # Get from Pulumi config object with default value
            try:
                # Try to get the config value for logging.level
                config_obj = self.config_manager.config.get_object("logging")
                if config_obj and "level" in config_obj:
                    log_level = config_obj["level"].lower()
                else:
                    log_level = "info"
            except Exception:
                # Default if not found in config
                log_level = "info"

        # Update log level of existing logging system
        self.log_manager.set_log_level(log_level)
        self.logger.info(f"Logging system updated with level: {log_level}")

    def _register_providers(self) -> None:
        """Register provider modules with the provider registry."""
        self.logger.info("Registering provider modules")

        # Discover available provider modules
        provider_modules = self.discover_provider_modules()
        self.logger.info(f"Discovered {len(provider_modules)} provider modules")

        # In MVP, we won't actually register any providers yet
        # This will be expanded in future implementations

    def discover_provider_modules(self) -> List[str]:
        """Discover available provider modules.

        Scans the providers directory for valid provider modules.

        Returns:
            List of provider module names.
        """
        self.logger.info("Discovering provider modules")

        # Get provider modules from discovery service
        providers = self.provider_discovery.discover_provider_modules()

        # In the MVP, this will return an empty list since no providers are implemented
        # TODO: develop provider discovery service
        return providers

    def _collect_git_metadata(self) -> Dict[str, Any]:
        """Collect Git repository metadata.

        Returns:
            Dictionary containing Git metadata.
        """
        self.logger.info("Collecting Git metadata")

        # In MVP, return basic metadata
        # This will be expanded in future implementations to actually query Git
        return {
            "repository": "example-repo",
            "branch": "main",
            "commit": "abc123",
            "commitTime": "unknown"
        }

    def _process_metadata(self, git_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process and combine all metadata.

        Args:
            git_metadata: Git repository metadata.

        Returns:
            Dictionary containing combined metadata.
        """
        self.logger.info("Processing metadata")

        # Get project configuration
        project_config = self.config_manager._get_project_config()

        # Combine metadata
        metadata = {
            "project": project_config,
            "git": git_metadata,
            "providers": {}
        }

        return metadata

    def run(self) -> bool:
        """Execute the core module workflow.

        Returns:
            Boolean indicating success (True) or failure (False).
        """
        self.logger.info("Starting Core Module execution")

        try:
            # Step 1: Register provider modules with registry
            self._register_providers()

            # Step 3: Collect Git metadata
            git_metadata = self._collect_git_metadata()

            # Step 4: Process metadata
            metadata = self._process_metadata(git_metadata)

            # Step 5: Generate stack outputs
            self._generate_stack_outputs(metadata)

            self.logger.info("Core Module execution completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Core Module execution failed: {str(e)}")
            # Add detailed error information in debug mode
            if self.log_manager.get_log_level() == "debug":
                import traceback
                msg = "Detailed error traceback:\n"
                self.logger.debug(f"{msg}{traceback.format_exc()}")
            # Re-raise to ensure Pulumi sees the error
            raise

    def _generate_stack_outputs(self, metadata: Dict[str, Any]) -> None:
        """Generate Pulumi stack outputs.

        Args:
            metadata: Metadata to include in the stack outputs.
        """
        self.logger.info("Generating stack outputs")

        # Output core module version and status
        pulumi.export("status", "success")

        # Output core module information
        pulumi.export("core", {
            "version": "0.1.0",
            "name": "core-module",
            "providers": metadata.get("providers", {}),
            "project": metadata.get("project", {})
        })
