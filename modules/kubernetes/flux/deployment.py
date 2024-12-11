from typing import Dict, Any, List
from pulumi import log, ResourceOptions, CustomTimeouts
import pulumi_kubernetes as k8s

from pulumi_kubernetes.helm.v4 import Chart

from ..deployment import KubernetesModule
from .types import FluxConfig
from modules.core.interfaces import ModuleDeploymentResult


class FluxModule(KubernetesModule):
    """Flux module implementation."""

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
        return version.lstrip("v") if version and version.startswith("v") else version

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        try:
            flux_config = FluxConfig(**config)
            operator_version = self.sanitize_version(flux_config.operator_version)

            log.info(f"Deploying Flux Operator {operator_version} from OCI registry...")

            # Deploy namespace (no strict parent, so it doesn't block teardown)
            namespace = k8s.core.v1.Namespace(
                f"{self.name}-system",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=flux_config.namespace,
                    labels={
                        "app.kubernetes.io/name": "flux",
                        "app.kubernetes.io/part-of": "flux",
                    },
                    annotations={
                        "fluxcd.controlplane.io/reconcile": "enabled",
                        "fluxcd.controlplane.io/reconcileEvery": "1h",
                        "fluxcd.controlplane.io/reconcileTimeout": "3m",
                    },
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=self.provider.provider
                ),
            )

            # Deploy storage PVC (child of namespace)
            storage_pvc = k8s.core.v1.PersistentVolumeClaim(
                f"{self.name}-storage",
                metadata=k8s.meta.v1.ObjectMetaArgs(name=f"{self.name}-storage", namespace=flux_config.namespace),
                spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                    access_modes=["ReadWriteOnce"],
                    resources=k8s.core.v1.ResourceRequirementsArgs(requests={"storage": flux_config.storage_size}),
                    storage_class_name=flux_config.storage_class,
                ),
                opts=ResourceOptions(provider=self.provider.provider, parent=namespace),
            )

            # Deploy Flux Operator chart with minimal deletion wait times
            operator_chart = Chart(
                "flux-operator",
                chart="oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator",
                version=operator_version,
                namespace=flux_config.namespace,
                values={
                    "operator": {
                        "create": True,
                        "resources": {
                            "limits": {"cpu": "200m", "memory": "256Mi"},
                            "requests": {"cpu": "100m", "memory": "128Mi"},
                        },
                    }
                },
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=storage_pvc,
                    custom_timeouts=CustomTimeouts(create="5m", update="5m", delete="10s"),
                ),
            )

            # Deploy FluxInstance CR with short delete timeout
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
                resources=[f"{self.name}-namespace", f"{self.name}-storage", "flux-operator", f"{self.name}-instance"],
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
