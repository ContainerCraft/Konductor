# ./modules/kubernetes/components/crossplane/deployment.py
"""
Crossplane component deployment implementation.

TODO:
- Migrate, add, and complete Crossplane component deployment logic implementation.
"""
from typing import Dict, Any, List
from pulumi import log, ResourceOptions

from ...resources.workload.namespace import create_namespace
from ...resources.workload.custom_resource import create_custom_resource
from ...resources.helm.chart import create_helm_chart
from ...resources.rbac.binding import create_cluster_role_binding
from ..base import KubernetesComponent
from .types import CrossplaneConfig
from modules.core.interfaces import ModuleDeploymentResult


class CrossplaneComponent(KubernetesComponent):
    """Crossplane component implementation."""

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
        """Deploy Crossplane system and related resources."""
        try:
            crossplane_config = CrossplaneConfig(**config)

            # Deploy namespace
            namespace = create_namespace(
                f"{self.name}-namespace",
                self.provider.provider,
                labels={
                    "app.kubernetes.io/name": "crossplane",
                    "app.kubernetes.io/part-of": "crossplane",
                },
            )

            # Configure Helm values
            helm_values = {
                "metrics": {
                    "enabled": crossplane_config.metrics_enabled,
                    "service": {"annotations": {"prometheus.io/scrape": "true", "prometheus.io/port": "8080"}},
                },
                "resourcesCrossplane": crossplane_config.resource_limits,
                "serviceAccount": {"create": True, "name": "crossplane"},
                "deploymentStrategy": "RollingUpdate",
                "rbacManager": {"deploy": True, "deploymentStrategy": "RollingUpdate"},
                "provider": {"packages": []},
                "args": [],
            }

            if crossplane_config.enable_external_secret_stores:
                helm_values["args"].append("--enable-external-secret-stores")
            if crossplane_config.enable_composition_revisions:
                helm_values["args"].append("--enable-composition-revisions")

            # Deploy Helm release
            repository_url = "https://charts.crossplane.io/stable"
            release = create_helm_chart(
                f"{self.name}-system",
                "crossplane",
                crossplane_config.namespace,
                crossplane_config.version,
                helm_values,
                self.provider.provider,
                repository=repository_url,
                atomic=True,
                cleanup_on_fail=True,
                timeout=600,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=namespace,
                    depends_on=[namespace],
                ),
            )

            # Create DeploymentRuntimeConfig
            runtime_config = create_custom_resource(
                "provider-helm-deployment-runtime-config",
                api_version="pkg.crossplane.io/v1beta1",
                kind="DeploymentRuntimeConfig",
                metadata={
                    "name": "provider-helm",
                    "namespace": crossplane_config.namespace,
                },
                spec={"serviceAccountTemplate": {"metadata": {"name": "provider-helm"}}},
                provider=self.provider.provider,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=release,
                    depends_on=[release],
                ),
            )

            # Create Provider
            provider_helm = create_custom_resource(
                "provider-helm",
                api_version="pkg.crossplane.io/v1",
                kind="Provider",
                metadata={
                    "name": "provider-helm",
                    "namespace": crossplane_config.namespace,
                },
                spec={
                    "package": "xpkg.upbound.io/crossplane-contrib/provider-helm:v0.17.0",
                    "runtimeConfigRef": {
                        "apiVersion": "pkg.crossplane.io/v1beta1",
                        "kind": "DeploymentRuntimeConfig",
                        "name": "provider-helm",
                    },
                },
                provider=self.provider.provider,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=runtime_config,
                    depends_on=[runtime_config],
                ),
            )

            # Create ClusterRoleBinding
            cluster_role_binding = create_cluster_role_binding(
                "provider-helm-cluster-admin",
                subjects=[
                    {"kind": "ServiceAccount", "name": "provider-helm", "namespace": crossplane_config.namespace}
                ],
                role_ref={"kind": "ClusterRole", "name": "cluster-admin", "apiGroup": "rbac.authorization.k8s.io"},
                provider=self.provider.provider,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=provider_helm,
                    depends_on=[provider_helm],
                ),
            )

            # Create ProviderConfig
            provider_config = create_custom_resource(
                "provider-helm-vcluster",
                api_version="helm.crossplane.io/v1beta1",
                kind="ProviderConfig",
                metadata={
                    "name": "provider-helm-vcluster",
                    "namespace": crossplane_config.namespace,
                },
                spec={
                    "credentials": {
                        "source": "Secret",
                        "secretRef": {"namespace": "vcluster-cluster", "name": "vcluster-kubeconfig", "key": "value"},
                    }
                },
                provider=self.provider.provider,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=provider_helm,
                    depends_on=[provider_helm],
                ),
            )

            return ModuleDeploymentResult(
                success=True,
                version=crossplane_config.version,
                resources=[
                    f"{self.name}-namespace",
                    f"{self.name}-system",
                    "provider-helm-deployment-runtime-config",
                    "provider-helm",
                    "provider-helm-cluster-admin",
                    "provider-helm-vcluster",
                ],
                metadata={
                    "namespace": crossplane_config.namespace,
                    "version": crossplane_config.version,
                },
            )

        except Exception as e:
            log.error(f"Failed to deploy Crossplane: {str(e)}")
            return ModuleDeploymentResult(success=False, version="", errors=[str(e)])
