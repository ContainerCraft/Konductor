# ./modules/core/interfaces.py
"""Shared interfaces and protocols for the core module."""

from typing import Protocol, Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceMetadata(BaseModel):
    """Common resource metadata."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)


class ModuleDeploymentResult(BaseModel):
    """
    Results from a module deployment operation.

    Attributes:
        success: Whether the deployment was successful
        version: Version of the deployed module
        resources: List of created resource names/IDs
        errors: List of error messages if any occurred
        metadata: Additional deployment metadata
    """

    success: bool
    version: Optional[str] = Field(default="")
    resources: List[str] = Field(default_factory=list, description="List of resource names/identifiers")
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class DeploymentContext(Protocol):
    """Protocol defining the deployment context interface."""

    def get_config(self) -> Dict[str, Any]: ...
    def deploy(self) -> ModuleDeploymentResult: ...


class ModuleInterface(Protocol):
    """Enhanced module interface with validation."""

    def validate_config(self, config: Dict[str, Any]) -> List[str]: ...
    def pre_deploy_check(self) -> List[str]: ...
    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult: ...
    def post_deploy_validation(self, result: ModuleDeploymentResult) -> List[str]: ...
    def get_dependencies(self) -> List[str]: ...


class ResourceManagerInterface(Protocol):
    """Protocol for resource managers."""

    def get_or_create(self) -> tuple[Any, Dict[str, Any]]: ...
    def deploy_resources(self) -> Dict[str, Any]: ...
