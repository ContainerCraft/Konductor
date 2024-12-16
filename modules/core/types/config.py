# ./modules/core/types/config.py
"""
Core module configuration types implementation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .metadata import StackConfig


class StackOutputs(BaseModel):
    """
    Complete stack outputs structure.

    Maps to the complete stack outputs JSON structure.
    """
    stack: StackConfig
    secrets: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sensitive information like credentials or tokens"
    )


class ModuleDefaults(BaseModel):
    """
    Default configuration for modules.

    Provides standard configuration defaults that can be overridden
    by specific module implementations.
    """
    enabled: bool = Field(
        default=False,
        description="Whether the module is enabled"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Module-specific configuration"
    )


class ConfigurationValidator(BaseModel):
    """Configuration validation interface."""
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        raise NotImplementedError
