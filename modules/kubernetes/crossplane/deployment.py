# ./modules/kubernetes/crossplane/deployment.py
from typing import Dict, Any, List
from pulumi import log, ResourceOptions, CustomTimeouts
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions import CustomResource

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
        """Deploy Crossplane system and related resources."""
        try:
            # Parse config
            crossplane_config = CrossplaneConfig(**config)

            # 1. Deploy namespace (crossplane-system)
            namespace = k8s.core.v1.Namespace(
                f"{self.name}-namespace",
                metadata={
                    "name": crossplane_config.namespace,
                    "labels": {
                        "app.kubernetes.io/name": "crossplane",
                        "app.kubernetes.io/part-of": "crossplane",
                    },
                },
                opts=ResourceOptions(
                    custom_timeouts=CustomTimeouts(create="5m", update="5m", delete="10s"),
                    provider=self.provider.provider,
                    parent=self.provider.provider,
                ),
            )

            # 2. Install Crossplane via Helm
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

            log.info(f"Deploying Crossplane Helm release to namespace {crossplane_config.namespace}")
            release = k8s.helm.v3.Release(
                f"{self.name}-system",
                k8s.helm.v3.ReleaseArgs(
                    chart="crossplane",
                    repository_opts=k8s.helm.v3.RepositoryOptsArgs(repo="https://charts.crossplane.io/stable"),
                    version=crossplane_config.version,
                    namespace=crossplane_config.namespace,
                    values=helm_values,
                    wait_for_jobs=True,
                    timeout=600,  # 10 minutes
                    cleanup_on_fail=True,
                    atomic=True,
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=namespace,
                    depends_on=[namespace],
                    custom_timeouts=CustomTimeouts(create="1200s", update="600s", delete="30s"),
                ),
            )

            # 3. Create DeploymentRuntimeConfig for provider-helm
            deployment_runtime_config = CustomResource(
                "provider-helm-deployment-runtime-config",
                api_version="pkg.crossplane.io/v1beta1",
                kind="DeploymentRuntimeConfig",
                metadata={
                    "name": "provider-helm",
                    "namespace": crossplane_config.namespace,
                },
                spec={"serviceAccountTemplate": {"metadata": {"name": "provider-helm"}}},
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=release,
                    depends_on=[release],
                ),
            )

            # 4. Create the Provider resource for provider-helm
            provider_helm = CustomResource(
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
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=deployment_runtime_config,
                    depends_on=[deployment_runtime_config],
                ),
            )

            # 5. Create ClusterRoleBinding for provider-helm SA
            # Using dictionary fields directly to avoid k8s.types
            cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
                "provider-helm-cluster-admin",
                metadata={"name": "provider-helm-cluster-admin"},
                subjects=[
                    {"kind": "ServiceAccount", "name": "provider-helm", "namespace": crossplane_config.namespace}
                ],
                role_ref={"kind": "ClusterRole", "name": "cluster-admin", "apiGroup": "rbac.authorization.k8s.io"},
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=provider_helm,
                    depends_on=[provider_helm],
                ),
            )

            # 6. Create ProviderConfig for the helm provider
            provider_helm_config = CustomResource(
                "provider-helm-vcluster-moo",
                api_version="helm.crossplane.io/v1beta1",
                kind="ProviderConfig",
                metadata={
                    "name": "provider-helm-vcluster-moo",
                    "namespace": crossplane_config.namespace,
                },
                spec={
                    "credentials": {
                        "source": "Secret",
                        "secretRef": {"namespace": "vcluster-moo-cluster", "name": "moo-kubeconfig", "key": "value"},
                    }
                },
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
                    "provider-helm-vcluster-moo",
                ],
                metadata={
                    "namespace": crossplane_config.namespace,
                    "version": crossplane_config.version,
                },
            )
        except Exception as e:
            log.error(f"Failed to deploy Crossplane and related resources: {str(e)}")
            return ModuleDeploymentResult(success=False, version="", errors=[str(e)])
