# src/core/providers/provider_discovery.py

"""Provider discovery for the core module."""

from typing import Dict, List, Any


class ProviderDiscovery:
    """Discovers and loads provider modules."""

    def __init__(self, log_manager):
        """Initialize the provider discovery.

        Args:
            log_manager: The log manager instance.
        """
        self.logger = log_manager.get_logger("provider_discovery")
        self.provider_modules = {}

    def discover_provider_modules(self) -> List[str]:
        """Discover available provider modules.

        Returns:
            List of discovered provider module names.
        """
        self.logger.info("Discovering provider modules")
        # In MVP, return an empty list
        return []

    def get_provider_modules(self) -> Dict[str, Any]:
        """Get all discovered provider modules.

        Returns:
            Dictionary of provider modules.
        """
        return self.provider_modules
