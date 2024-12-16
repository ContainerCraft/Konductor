# ./modules/kubernetes/components/flux/deployment.py
from typing import Dict, Any, List
from pulumi import log, ResourceOptions, CustomTimeouts
import pulumi_kubernetes as k8s

from ...resources.workload.namespace import create_namespace
from ...resources.storage.pvc import create_persistent_volume_claim
from ...resources.helm.chart import create_helm_chart
from ..base import KubernetesComponent
from .types import FluxConfig
from modules.core.interfaces import ModuleDeploymentResult


class FluxComponent(KubernetesComponent):
    """Flux component implementation."""

    def __init__(self, init_config):
        super().__init__(init_config)
        self.name = "flux"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        try:
            if config is None:
                config = {}
            FluxConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def sanitize_version(self, version: str) -> str:
        """Sanitize version string by removing 'v' prefix if present."""
        return version.lstrip("v") if version and version.startswith("v") else version

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        try:
            flux_config = FluxConfig(**config)
            operator_version = self.sanitize_version(flux_config.operator_version)

            log.info(f"Deploying Flux Operator {operator_version} from OCI registry...")

            # Create namespace
            namespace = create_namespace(
                f"{self.name}-system",
                self.provider.provider,
                labels={
                    "app.kubernetes.io/name": "flux",
                    "app.kubernetes.io/part-of": "flux",
                },
                annotations={
                    "fluxcd.controlplane.io/reconcile": "enabled",
                    "fluxcd.controlplane.io/reconcileEvery": "1h",
                    "fluxcd.controlplane.io/reconcileTimeout": "3m",
                },
            )

            # Create storage PVC
            storage_pvc = create_persistent_volume_claim(
                f"{self.name}-storage",
                flux_config.namespace,
                flux_config.storage_class,
                flux_config.storage_size,
                self.provider.provider,
                opts=ResourceOptions(provider=self.provider.provider, parent=namespace),
            )

            # Deploy Flux Operator chart
            operator_chart = create_helm_chart(
                "flux-operator",
                "oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator",
                flux_config.namespace,
                operator_version,
                {
                    "operator": {
                        "create": True,
                        "resources": {
                            "limits": {"cpu": "200m", "memory": "256Mi"},
                            "requests": {"cpu": "100m", "memory": "128Mi"},
                        },
                    }
                },
                self.provider.provider,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=storage_pvc,
                ),
            )

            # Deploy FluxInstance CR
            flux_instance = k8s.apiextensions.CustomResource(
                f"{self.name}-instance",
                api_version="fluxcd.controlplane.io/v1",
                kind="FluxInstance",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name="flux",
                    namespace=flux_config.namespace,
                    annotations={
                        "fluxcd.controlplane.io/reconcile": "enabled",
                        "fluxcd.controlplane.io/reconcileEvery": flux_config.reconcile_interval,
                        "fluxcd.controlplane.io/reconcileTimeout": flux_config.reconcile_timeout,
                    },
                ),
                spec={
                    "distribution": {"version": flux_config.version, "registry": "ghcr.io/fluxcd"},
                    "components": flux_config.components,
                    "cluster": {
                        "type": "kubernetes",
                        "multitenant": flux_config.multitenant,
                        "networkPolicy": flux_config.network_policy,
                        "domain": flux_config.cluster_domain,
                    },
                    "storage": {"class": flux_config.storage_class, "size": flux_config.storage_size},
                    "kustomize": {
                        "patches": [
                            {
                                "target": {"kind": "Deployment", "name": "(kustomize-controller|helm-controller)"},
                                "patch": f"""
                                    - op: add
                                      path: /spec/template/spec/containers/0/args/-
                                      value: --concurrent={flux_config.concurrent_reconciles}
                                    - op: add
                                      path: /spec/template/spec/containers/0/args/-
                                      value: --requeue-dependency={flux_config.requeue_dependency_interval}
                                """,
                            }
                        ]
                    },
                },
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=operator_chart,
                    custom_timeouts=CustomTimeouts(create="5m", update="5m", delete="10s"),
                ),
            )

            return ModuleDeploymentResult(
                success=True,
                version=flux_config.version,
                resources=[
                    f"{self.name}-namespace",
                    f"{self.name}-storage",
                    "flux-operator",
                    f"{self.name}-instance"
                ],
                metadata={
                    "namespace": flux_config.namespace,
                    "version": flux_config.version,
                    "components": flux_config.components,
                    "storage_pvc": storage_pvc.metadata.name,
                },
            )

        except Exception as e:
            log.error(f"Failed to deploy Flux: {str(e)}")
            return ModuleDeploymentResult(success=False, version="", errors=[str(e)])
