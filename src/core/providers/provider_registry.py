# src/core/providers/provider_registry.py

"""Provider registry for the core module."""

from typing import Dict, Any, Optional, Callable


class ProviderRegistry:
    """Registry for all providers."""

    def __init__(self, log_manager):
        """Initialize the provider registry.

        Args:
            log_manager: The log manager instance.
        """
        self.logger = log_manager.get_logger("provider_registry")
        self.provider_factories = {}
        self.providers = {}

    def register_provider_factory(
        self, provider_type: str, factory_func: Callable
    ) -> None:
        """Register a provider factory function.

        Args:
            provider_type: The type of provider (e.g., 'aws', 'azure').
            factory_func: The factory function to create providers of this type.
        """
        self.logger.info(f"Registering factory for provider type: {provider_type}")
        self.provider_factories[provider_type] = factory_func

    def create_provider(
        self, provider_type: str, provider_name: str, **kwargs
    ) -> Optional[Any]:
        """Create a provider instance.

        Args:
            provider_type: The type of provider (e.g., 'aws', 'azure').
            provider_name: The name of the provider instance.
            **kwargs: Additional arguments to pass to the factory function.

        Returns:
            The created provider instance, or None if creation failed.
        """
        self.logger.info(f"Creating provider: {provider_type}/{provider_name}")

        # Check if factory exists for this provider type
        if provider_type not in self.provider_factories:
            self.logger.error(f"No factory registered for provider type: {provider_type}")
            return None

        # Create the provider instance
        try:
            factory = self.provider_factories[provider_type]
            provider = factory(provider_name=provider_name, **kwargs)

            # Register the provider in the registry
            if provider_type not in self.providers:
                self.providers[provider_type] = {}

            self.providers[provider_type][provider_name] = provider
            return provider
        except Exception as e:
            self.logger.error(
                f"Failed to create provider: {provider_type}/{provider_name}. Error: {str(e)}"
            )
            return None

    def get_provider(self, provider_type: str, provider_name: str) -> Optional[Any]:
        """Get a provider instance by type and name.

        Args:
            provider_type: The type of provider (e.g., 'aws', 'azure').
            provider_name: The name of the provider instance.

        Returns:
            The provider instance, or None if not found.
        """
        if (
            provider_type in self.providers
            and provider_name in self.providers[provider_type]
        ):
            return self.providers[provider_type][provider_name]
        return None
