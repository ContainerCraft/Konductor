# ./modules/core/metadata.py

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It provides a thread-safe singleton for consistent metadata management
across all resources in a Pulumi program.
"""

from typing import Dict, Optional, ClassVar, Any, Protocol
from pydantic import ValidationError
from datetime import datetime, timezone
from threading import Lock

import pulumi
from pulumi import Config, log

from .compliance_types import ComplianceConfig


class MetadataSingleton:
    """
    Thread-safe singleton class to manage global metadata.
    Provides a centralized store for all module metadata, with each module
    storing its metadata under its own namespace.
    """

    _instance: Optional["MetadataSingleton"] = None
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls) -> "MetadataSingleton":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        """Initialize metadata storage."""
        if not hasattr(self, "_initialized"):
            self._global_labels: Dict[str, str] = {}
            self._global_annotations: Dict[str, str] = {}
            self._git_metadata: Dict[str, Any] = {}
            self._modules_metadata: Dict[str, Dict[str, Any]] = {}
            self._initialized = True

    @property
    def global_labels(self) -> Dict[str, str]:
        """Get global labels."""
        with self._lock:
            return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        """Get global annotations."""
        with self._lock:
            return self._global_annotations.copy()

    @property
    def git_metadata(self) -> Dict[str, Any]:
        """Get Git metadata."""
        with self._lock:
            return self._git_metadata.copy()

    @property
    def modules_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all modules metadata."""
        with self._lock:
            return self._modules_metadata.copy()

    def set_labels(self, labels: Dict[str, str]) -> None:
        """Set global labels."""
        with self._lock:
            self._global_labels.update(labels)

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        """Set global annotations."""
        with self._lock:
            self._global_annotations.update(annotations)

    def set_git_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set Git metadata."""
        with self._lock:
            self._git_metadata.update(metadata)

    def set_module_metadata(self, module_name: str, metadata: Dict[str, Any]) -> None:
        """
        Set metadata for a specific module.
        Each module's metadata is stored under its own namespace.
        """
        with self._lock:
            if module_name not in self._modules_metadata:
                self._modules_metadata[module_name] = {}
            self._modules_metadata[module_name].update(metadata)

    def get_module_metadata(self, module_name: str) -> Dict[str, Any]:
        """Get metadata for a specific module."""
        with self._lock:
            return self._modules_metadata.get(module_name, {}).copy()


class InitConfig(Protocol):
    project_name: str
    stack_name: str
    git_info: Any
    metadata: Dict[str, Dict[str, str]]


def setup_global_metadata(init_config: InitConfig) -> None:
    """Initialize global metadata for resources."""
    try:
        metadata = MetadataSingleton()

        # Create base labels
        base_labels = {
            "managed-by": "konductor",
            "project": init_config.project_name,
            "stack": init_config.stack_name,
        }

        # Create git metadata labels
        git_info = init_config.git_info.model_dump()
        git_labels = {
            "git.commit": git_info["commit_hash"],
            "git.branch": git_info["branch_name"],
            "git.repository": git_info["remote_url"],
        }

        # Merge all labels
        all_labels = {
            **base_labels,
            **git_labels,
            **(init_config.metadata.get("labels", {})),
        }

        # Set global metadata
        metadata.set_labels(all_labels)
        metadata.set_annotations(init_config.metadata.get("annotations", {}))
        metadata.set_git_metadata(git_info)

        log.info("Global metadata initialized successfully")

    except Exception as e:
        log.error(f"Failed to setup global metadata: {str(e)}")
        raise


def get_compliance_metadata() -> ComplianceConfig:
    """
    Get compliance metadata from the global singleton.
    """
    try:
        metadata = MetadataSingleton()
        if compliance_metadata := metadata.get_module_metadata("compliance"):
            try:
                return ComplianceConfig.model_validate(compliance_metadata)
            except ValidationError as e:
                log.error(f"Compliance metadata validation error: {str(e)}")
                # Try parsing with more lenient validation
                return ComplianceConfig.from_pulumi_config(Config(), datetime.now(timezone.utc))
        return ComplianceConfig()
    except Exception as e:
        log.error(f"Failed to get compliance metadata: {str(e)}")
        return ComplianceConfig()


def export_compliance_metadata() -> None:
    """
    Export compliance metadata to Pulumi stack outputs.
    Uses metadata from the global singleton.
    """
    try:
        log.info("Exporting compliance metadata")
        metadata_singleton = MetadataSingleton()

        # Get compliance metadata
        compliance_metadata = get_compliance_metadata()

        # Get Git metadata
        git_metadata = metadata_singleton.git_metadata
        git_info = {
            "branch": git_metadata.get("branch_name", "unknown"),
            "commit": git_metadata.get("commit_hash", "unknown"),
            "remote": git_metadata.get("remote_url", "unknown"),
        }

        # Create the compliance export structure
        stack_outputs = {
            "config": {
                "compliance": compliance_metadata.to_dict(),
                "source_repository": git_info,
            }
        }

        # Export the stack outputs
        pulumi.export("stack_outputs", stack_outputs)
        log.info("Successfully exported compliance metadata")

    except Exception as e:
        log.error(f"Failed to export compliance metadata: {str(e)}")
        raise
