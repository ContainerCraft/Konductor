# modules/kubernetes/crossplane/deployment.py
from typing import Dict, Any, List
from pulumi import log, ResourceOptions
import pulumi_kubernetes as k8s

from ..deployment import KubernetesModule
from .types import CrossplaneConfig
from modules.core.interfaces import ModuleDeploymentResult


class CrossplaneModule(KubernetesModule):
    """Crossplane module implementation."""

    def __init__(self, init_config):
        super().__init__(init_config)
        self.name = "crossplane"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Crossplane configuration."""
        try:
            if config is None:
                config = {}
            CrossplaneConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy Crossplane system."""
        try:
            # Parse config
            crossplane_config = CrossplaneConfig(**config)

            # Deploy namespace
            namespace = k8s.core.v1.Namespace(
                f"{self.name}-namespace",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=crossplane_config.namespace,
                    labels={
                        "app.kubernetes.io/name": "crossplane",
                        "app.kubernetes.io/part-of": "crossplane",
                    }
                ),
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Configure Helm values
            helm_values = {
                "metrics": {
                    "enabled": True,
                },
                "resourcesCrossplane": crossplane_config.resource_limits,
                "serviceAccount": {
                    "create": True,
                    "name": "crossplane"
                },
                "provider": {
                    "packages": []
                }
            }

            # Add feature flags if enabled
            if crossplane_config.enable_external_secret_stores:
                helm_values["args"] = ["--enable-external-secret-stores"]
            if crossplane_config.enable_composition_revisions:
                helm_values["args"] = helm_values.get("args", []) + ["--enable-composition-revisions"]

            # Deploy Helm release
            log.info(f"Deploying Crossplane Helm release to namespace {crossplane_config.namespace}")
            release = k8s.helm.v3.Release(
                f"{self.name}-system",
                k8s.helm.v3.ReleaseArgs(
                    chart="crossplane",
                    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                        repo="https://charts.crossplane.io/stable"
                    ),
                    version=crossplane_config.version,
                    namespace=crossplane_config.namespace,
                    values=helm_values,
                    wait_for_jobs=True,
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=namespace,
                    depends_on=[namespace],
                ),
            )

            return ModuleDeploymentResult(
                success=True,
                version=crossplane_config.version,
                resources=[
                    f"{self.name}-namespace",
                    f"{self.name}-system",
                ],
                metadata={
                    "namespace": crossplane_config.namespace,
                    "version": crossplane_config.version,
                }
            )

        except Exception as e:
            log.error(f"Failed to deploy Crossplane: {str(e)}")
            return ModuleDeploymentResult(
                success=False,
                version="",
                errors=[str(e)]
            )
