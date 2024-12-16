# ./modules/core/types/metadata.py
"""
Core module metadata types implementation.

This module defines all shared data classes and types used across all modules.
It provides type-safe configuration structures using Pydantic models and TypedDict.

TODO:
- Migrate, add, and complete metadata types for core module.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .base import ResourceBase
from .compliance import ComplianceConfig


class GlobalMetadata(BaseModel):
    """
    Global metadata structure.

    Maps to the 'metadata' section of stack outputs.
    """
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Global public cloud resource tags"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Global Kubernetes labels"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Global Kubernetes annotations"
    )


class SourceRepository(BaseModel):
    """Source repository information."""
    branch: str
    commit: str
    remote: str
    tag: Optional[str] = None


class StackConfig(BaseModel):
    """
    Root stack configuration.

    Maps to the root level of stack outputs.
    """
    compliance: ComplianceConfig
    metadata: GlobalMetadata
    source_repository: SourceRepository
    k8s_component_versions: Dict[str, Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Versions of Kubernetes components"
    )


class ResourceMetadata(ResourceBase):
    """
    Resource metadata structure.

    Attributes:
        tags (Dict[str, str]): Resource tags
        labels (Dict[str, str]): Resource labels
        annotations (Dict[str, str]): Resource annotations
        created_at (datetime): Resource creation timestamp
        updated_at (datetime): Resource last update timestamp
    """
    tags: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
