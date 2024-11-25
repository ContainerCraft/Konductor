# ../konductor/modules/core/metadata.py

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It provides a thread-safe singleton for consistent metadata management
across all resources in a Pulumi program.
"""

import threading
from typing import Dict, Optional, ClassVar
from pulumi import log
from threading import Lock

from .types import InitializationConfig


class MetadataSingleton:
    """
    Thread-safe singleton class to manage global metadata.

    This class ensures consistent labels and annotations across all resources.
    It uses threading.Lock for thread safety and provides atomic operations
    for metadata updates.

    Attributes:
        _instance: The singleton instance
        _lock: Thread lock for synchronization
        _global_labels: Dictionary of global labels
        _global_annotations: Dictionary of global annotations
    """
    _instance: Optional['MetadataSingleton'] = None
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls) -> 'MetadataSingleton':
        """
        Ensure only one instance is created.

        Returns:
            MetadataSingleton: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        """Initialize metadata storage."""
        if not hasattr(self, '_initialized'):
            self._global_labels: Dict[str, str] = {}
            self._global_annotations: Dict[str, str] = {}
            self._initialized = True

    @property
    def global_labels(self) -> Dict[str, str]:
        """
        Get global labels.

        Returns:
            Dict[str, str]: Copy of global labels dictionary
        """
        with self._lock:
            return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        """
        Get global annotations.

        Returns:
            Dict[str, str]: Copy of global annotations dictionary
        """
        with self._lock:
            return self._global_annotations.copy()

    def set_labels(self, labels: Dict[str, str]) -> None:
        """
        Set global labels.

        Args:
            labels: Dictionary of labels to set
        """
        with self._lock:
            self._global_labels.update(labels)

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        """
        Set global annotations.

        Args:
            annotations: Dictionary of annotations to set
        """
        with self._lock:
            self._global_annotations.update(annotations)

def setup_global_metadata(init_config: InitializationConfig) -> None:
    """
    Initialize global metadata for resources.

    Args:
        init_config: Initialization configuration object
    """
    try:
        metadata = MetadataSingleton()

        # Create base labels
        base_labels = {
            "managed-by": "konductor",
            "project": init_config.project_name,
            "stack": init_config.stack_name
        }

        # Create git metadata labels
        git_labels = {
            "git.commit": init_config.git_info.commit_hash,
            "git.branch": init_config.git_info.branch_name,
            "git.repository": init_config.git_info.remote_url
        }

        # Merge all labels
        all_labels = {
            **base_labels,
            **git_labels,
            **(init_config.metadata.get("labels", {}))
        }

        # Set global metadata
        metadata.set_labels(all_labels)
        metadata.set_annotations(init_config.metadata.get("annotations", {}))

        log.info("Global metadata initialized successfully")

    except Exception as e:
        log.error(f"Failed to setup global metadata: {str(e)}")
        raise

def set_global_labels(labels: Dict[str, str]) -> None:
    """Sets global labels."""
    MetadataSingleton().set_labels(labels)

def set_global_annotations(annotations: Dict[str, str]) -> None:
    """Sets global annotations."""
    MetadataSingleton().set_annotations(annotations)
