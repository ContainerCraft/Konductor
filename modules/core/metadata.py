# ../konductor/modules/core/metadata.py

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It includes functions to generate compliance and Git-related metadata.
"""

import threading
from typing import Dict, Optional, ClassVar
from pulumi import log

from .types import InitializationConfig

def setup_global_metadata(init_config: InitializationConfig) -> None:
    """
    Initialize global metadata for resources.

    Args:
        init_config: Initialization configuration object
    """
    try:
        # Get metadata from init_config
        metadata = init_config.metadata or {}

        # Create git metadata labels
        git_labels = {
            "git.commit": init_config.git_info.commit_hash,
            "git.branch": init_config.git_info.branch_name,
            "git.repository": init_config.git_info.remote_url
        }

        # Merge git metadata with existing labels
        labels = {
            **git_labels,
            **(metadata.get("labels", {}))
        }

        # Set global metadata
        set_global_labels(labels)
        set_global_annotations(metadata.get("annotations", {}))

        log.info(f"Global metadata initialized with git info: commit={git_labels['git.commit']}, branch={git_labels['git.branch']}")

    except Exception as e:
        log.error(f"Failed to setup global metadata: {str(e)}")
        raise


class MetadataSingleton:
    """
    Thread-safe singleton class to manage global metadata.
    Ensures consistent labels and annotations across all resources.
    """
    _instance: ClassVar[Optional['MetadataSingleton']] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        """Initialize metadata storage."""
        self._global_labels: Dict[str, str] = {}
        self._global_annotations: Dict[str, str] = {}

    def __new__(cls) -> 'MetadataSingleton':
        """Ensure only one instance is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()
                    cls._instance = instance
        return cls._instance

    @property
    def global_labels(self) -> Dict[str, str]:
        """Get global labels."""
        return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        """Get global annotations."""
        return self._global_annotations.copy()

    def set_labels(self, labels: Dict[str, str]) -> None:
        """Set global labels."""
        self._global_labels = labels.copy()

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        """Set global annotations."""
        self._global_annotations = annotations.copy()


def set_global_labels(labels: Dict[str, str]) -> None:
    """
    Sets global labels.

    Args:
        labels: The global labels to set.
    """
    MetadataSingleton().set_labels(labels)


def set_global_annotations(annotations: Dict[str, str]) -> None:
    """
    Sets global annotations.

    Args:
        annotations: The global annotations to set.
    """
    MetadataSingleton().set_annotations(annotations)
