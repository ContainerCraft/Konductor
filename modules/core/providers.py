# ./modules/core/providers.py
"""
Core module providers implementation.

TODO:
- Relocate provider specific logic into the correct module and submodule layout. (completed)
- Implement provider-agnostic cloud_providers dict or other provider-agnostic logic if required.
"""
from typing import Protocol, Dict, Any


class CloudProvider(Protocol):
    """Provider-agnostic interface for cloud providers."""

    def get_provider(self) -> Any: ...
    def get_region(self) -> str: ...
    def get_metadata(self) -> Dict[str, Any]: ...
