# ./modules/core/metadata.py

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It provides a thread-safe singleton for consistent metadata management
across all resources in a Pulumi program.
"""

from typing import Dict, Optional, ClassVar, Any, Protocol
from pulumi import log
from threading import Lock
from datetime import datetime

from .compliance_types import (
    Fisma,
    FismaAto,
    Nist,
    Scip,
    ScipProvider,
    ComplianceConfig,
    ScipOwnership,
)
import pulumi


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
        _aws_metadata: Dictionary of AWS metadata
        _git_metadata: Dictionary of Git metadata
    """

    _instance: Optional["MetadataSingleton"] = None
    _lock: ClassVar[Lock] = Lock()

    def __new__(cls) -> "MetadataSingleton":
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
        if not hasattr(self, "_initialized"):
            self._global_labels: Dict[str, str] = {}
            self._global_annotations: Dict[str, str] = {}
            self._aws_metadata: Dict[str, Any] = {}
            self._git_metadata: Dict[str, Any] = {}
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

    @property
    def aws_metadata(self) -> Dict[str, Any]:
        """Get AWS metadata."""
        with self._lock:
            return self._aws_metadata.copy()

    @property
    def git_metadata(self) -> Dict[str, Any]:
        """Get Git metadata."""
        with self._lock:
            return self._git_metadata.copy()

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

    def set_aws_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set AWS metadata."""
        with self._lock:
            self._aws_metadata.update(metadata)

    def set_git_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set Git metadata."""
        with self._lock:
            self._git_metadata.update(metadata)


class InitConfig(Protocol):
    project_name: str
    stack_name: str
    git_info: Any
    metadata: Dict[str, Dict[str, str]]


def setup_global_metadata(init_config: InitConfig) -> None:
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


def get_compliance_metadata() -> ComplianceConfig:
    """Get default compliance metadata"""
    # TODO: HIGH PRIORITY: Replace with pulumi stack config derived metadata instead of hard coded values. Consider adding support for non-ato values when developing against pre-prod compliance metadata.
    return ComplianceConfig(
        fisma=Fisma(
            ato=FismaAto(
                authorized=datetime.strptime("2025-03-27T00:00:00", "%Y-%m-%dT%H:%M:%S"),
                renew=datetime.strptime("2026-03-27T00:00:00", "%Y-%m-%dT%H:%M:%S"),
                review=datetime.strptime("2028-03-27T00:00:00", "%Y-%m-%dT%H:%M:%S"),
            ),
            enabled=True,
            level="moderate",
        ),
        nist=Nist(
            auxiliary=["ac-6.1", "ac-2.13"],
            controls=["ac-1"],
            enabled=True,
            exceptions=["ca-7.1", "ma-2.2", "si-12"],
        ),
        scip=Scip(
            environment="prod",
            ownership={
                "operator": ScipOwnership(
                    contacts=["seti2@nasa.gov", "alien51@nasa.gov"],
                    name="science-team-seti2-obs2819",
                ),
                "provider": ScipOwnership(
                    contacts=["scip@nasa.gov", "bobert@nasa.gov"],
                    name="scip-team-xyz",
                ),
            },
            provider=ScipProvider(name="Kubevirt", regions=["scip-west-1", "scip-east-1", "scip-lunar-2"]),
        ),
    )


def export_compliance_metadata():
    """Export compliance metadata to Pulumi stack outputs."""
    try:
        log.info("Exporting compliance metadata")
        metadata = get_compliance_metadata()
        metadata_singleton = MetadataSingleton()

        # Get Git metadata with fallbacks
        git_info = metadata_singleton.git_metadata
        git_metadata = {
            "branch": git_info.get("branch_name", "unknown"),
            "commit": git_info.get("commit_hash", "unknown"),
            "remote": git_info.get("remote_url", "unknown"),
        }

        # Get AWS metadata with fallbacks
        aws_metadata = metadata_singleton.aws_metadata or {
            "aws_user_account_id": "unknown",
            "aws_user_id": "unknown",
            "aws_user_arn": "unknown",
        }

        # Create the compliance export structure
        # TODO: HIGH PRIORITY: Replace ato date valueswith pulumi stack config derived
        #       metadata instead of hard coded values. Consider adding support for
        #       non-ato values when developing against pre-prod compliance metadata.
        stack_outputs = {
            "config": {
                "compliance": {
                    "fisma": {
                        "ato": {
                            "authorized": metadata.fisma.ato.authorized.strftime("%Y-%m-%dT%H:%M:%S"),
                            "renew": metadata.fisma.ato.renew.strftime("%Y-%m-%dT%H:%M:%S"),
                            "review": metadata.fisma.ato.review.strftime("%Y-%m-%dT%H:%M:%S"),
                        },
                        "enabled": metadata.fisma.enabled,
                        "level": metadata.fisma.level,
                    },
                    "nist": {
                        "auxiliary": metadata.nist.auxiliary,
                        "controls": metadata.nist.controls,
                        "enabled": metadata.nist.enabled,
                        "exceptions": metadata.nist.exceptions,
                    },
                    "scip": {
                        "environment": metadata.scip.environment,
                        "ownership": {
                            "operator": vars(metadata.scip.ownership["operator"]),
                            "provider": vars(metadata.scip.ownership["provider"]),
                        },
                        "provider": {
                            "name": metadata.scip.provider.name,
                            "regions": metadata.scip.provider.regions,
                        },
                    },
                },
                "aws": {
                    "sts_caller_identity": aws_metadata,
                },
                "source_repository": git_metadata,
            }
        }

        # Export the full stack outputs
        pulumi.export("stack_outputs", stack_outputs)
        log.info("Successfully exported compliance metadata")

    except Exception as e:
        log.error(f"Failed to export compliance metadata: {str(e)}")
        raise
