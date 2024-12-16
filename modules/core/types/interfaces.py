# ./modules/core/types/interfaces.py
"""
Core module interfaces implementation.
"""
from typing import Dict, Any, List, Protocol
from pydantic import BaseModel

from .base import ResourceBase, ConfigBase


class ModuleDeploymentResult(BaseModel):
    """
    Module deployment outputs.

    Attributes:
        config (List[ResourceBase]): Configurations returned for use by other modules and stacks.
        compliance (List[str]): Compliance and traceability reporting metadata.
        resources (Dict[str, Any]): Resources created by the module for users to interact with.
    """

    config: List[ResourceBase]
    compliance: List[str]
    resources: Dict[str, Any]


class DeploymentContext(Protocol):
    """Deployment context interface."""

    def get_config(self) -> ConfigBase: ...
    def deploy(self) -> ModuleDeploymentResult: ...


class ModuleInterface(Protocol):
    """Base interface for all modules."""

    def validate_config(self, config: ConfigBase) -> List[str]: ...
    def validate_resources(self, resources: List[ResourceBase]) -> List[str]: ...
    def deploy(self, config: ConfigBase) -> ModuleDeploymentResult: ...


class ResourceManagerInterface(Protocol):
    """Interface for resource managers."""

    def get_or_create(self) -> tuple[ResourceBase, Dict[str, Any]]: ...
    def deploy_resources(self) -> Dict[str, ResourceBase]: ...
