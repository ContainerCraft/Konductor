# ./modules/kubernetes/components/base.py
"""
Base class for Kubernetes components.
"""
"""
Base component class for Kubernetes components.
"""
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import pulumi_kubernetes as k8s
from pulumi import ResourceOptions, log

from ..types import KubernetesSubmoduleConfig, ComponentStatus, KubernetesMetadata
from modules.core.interfaces import ModuleDeploymentResult
from modules.core.types import InitializationConfig


class KubernetesComponent(ABC):
    """
    Base class for all Kubernetes components.

    Provides common functionality for:
    - Provider management
    - Metadata handling
    - Resource lifecycle
    - Error handling
    - Status tracking
    """

    def __init__(self, init_config: InitializationConfig):
        """Initialize the component."""
        self.init_config = init_config
        self.name: str = self.__class__.__name__.lower()
        self._provider: Optional[k8s.Provider] = None
        self._status = ComponentStatus()
        self._metadata = KubernetesMetadata()

    @property
    def provider(self) -> k8s.Provider:
        """Get the Kubernetes provider."""
        if not self._provider:
            raise RuntimeError(f"Provider not initialized for component {self.name}")
        return self._provider

    @property
    def status(self) -> ComponentStatus:
        """Get component status."""
        return self._status

    def set_provider(self, provider: k8s.Provider) -> None:
        """Set the Kubernetes provider."""
        self._provider = provider

    def update_metadata(self, metadata: KubernetesMetadata) -> None:
        """Update component metadata."""
        self._metadata = metadata

    def get_resource_opts(
        self,
        parent: Optional[Any] = None,
        depends_on: Optional[List[Any]] = None,
        additional_opts: Optional[Dict[str, Any]] = None,
    ) -> ResourceOptions:
        """
        Get standard resource options with metadata.

        Args:
            parent: Optional parent resource
            depends_on: Optional dependencies
            additional_opts: Additional ResourceOptions parameters

        Returns:
            ResourceOptions: Configured options for resource creation
        """
        opts = {
            "provider": self.provider,
            "parent": parent,
            "depends_on": depends_on or [],
        }
        if additional_opts:
            opts.update(additional_opts)
        return ResourceOptions(**opts)

    def get_metadata(self, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get resource metadata with standard labels and annotations.

        Args:
            additional_metadata: Additional metadata to include

        Returns:
            Dict[str, Any]: Complete metadata configuration
        """
        metadata = {
            "labels": {
                "app.kubernetes.io/name": self.name,
                "app.kubernetes.io/managed-by": "pulumi",
                "app.kubernetes.io/created-by": self.__class__.__name__,
                **self._metadata.labels,
            },
            "annotations": {
                "pulumi.com/created": datetime.now(timezone.utc).isoformat(),
                **self._metadata.annotations,
            },
        }

        if additional_metadata:
            metadata["labels"].update(additional_metadata.get("labels", {}))
            metadata["annotations"].update(additional_metadata.get("annotations", {}))

        return metadata

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate component configuration.

        Args:
            config: Configuration to validate

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        pass

    @abstractmethod
    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """
        Deploy the component.

        Args:
            config: Component configuration

        Returns:
            ModuleDeploymentResult: Deployment result
        """
        pass

    def pre_deploy(self, config: Dict[str, Any]) -> List[str]:
        """
        Pre-deployment validation and setup.

        Args:
            config: Component configuration

        Returns:
            List[str]: List of validation errors
        """
        self._status.state = "pending"
        self._status.start_time = datetime.now(timezone.utc)
        return self.validate_config(config)

    def post_deploy(self, success: bool, error: Optional[str] = None) -> None:
        """
        Post-deployment cleanup and status update.

        Args:
            success: Whether deployment was successful
            error: Optional error message
        """
        self._status.end_time = datetime.now(timezone.utc)
        self._status.state = "completed" if success else "failed"
        if error:
            self._status.message = error
            log.error(f"Component {self.name} deployment failed: {error}")

    def handle_error(self, e: Exception) -> ModuleDeploymentResult:
        """
        Standard error handling for component operations.

        Args:
            e: Exception that occurred

        Returns:
            ModuleDeploymentResult: Error result
        """
        error_msg = f"Failed to deploy component {self.name}: {str(e)}"
        log.error(error_msg)
        self.post_deploy(success=False, error=error_msg)
        return ModuleDeploymentResult(
            success=False, version="", errors=[error_msg], metadata={"status": self.status.dict()}
        )
