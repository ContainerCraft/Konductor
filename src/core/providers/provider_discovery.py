# src/core/providers/provider_discovery.py

"""Provider discovery for the core module."""

import os
from pathlib import Path
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

        # Get the path to the providers directory
        providers_dir = Path(os.path.dirname(__file__)).parent.parent / "providers"

        # Check if the providers directory exists
        if not providers_dir.exists() or not providers_dir.is_dir():
            self.logger.warning(f"Providers directory not found: {providers_dir}")
            return []

        provider_names = []

        # Scan for provider modules (directories with __init__.py files)
        for item in providers_dir.iterdir():
            if not item.is_dir():
                continue

            # Skip special directories
            if item.name.startswith("__") or item.name.startswith("."):
                continue

            # Check if this is a valid provider module (has __init__.py)
            init_py = item / "__init__.py"
            if init_py.exists():
                provider_names.append(item.name)

                # Try to import and cache the module (for future use)
                self._try_import_provider(item.name, init_py)

        return provider_names

    def _try_import_provider(self, provider_name: str, init_py_path: Path) -> None:
        """Try to import a provider module.

        Args:
            provider_name: Name of the provider module.
            init_py_path: Path to the __init__.py file.
        """
        try:
            # In MVP, we'll just log that we found the provider
            # In future implementations, we'll actually import the module
            self.logger.info(f"Found provider module: {provider_name}")
        except Exception as e:
            self.logger.error(
                f"Failed to import provider module {provider_name}: "
                f"{str(e)}"
            )

    def get_provider_modules(self) -> Dict[str, Any]:
        """Get all discovered provider modules.

        Returns:
            Dictionary of provider modules.
        """
        return self.provider_modules
