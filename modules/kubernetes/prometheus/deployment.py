# ./modules/prometheus/deployment.py

"""
Deploys the Prometheus module following the shared design patterns.
"""

from typing import Dict, Any, List
from pulumi import log, ResourceOptions
import pulumi_kubernetes as k8s

from ..deployment import KubernetesModule
from ..types import KubernetesConfig
from .types import PrometheusConfig
from modules.core.interfaces import ModuleDeploymentResult

class PrometheusModule(KubernetesModule):
    """Prometheus module implementation."""

    def __init__(self, init_config):
        super().__init__(init_config)
        self.name = "prometheus"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Prometheus configuration."""
        try:
            if config is None:
                config = {}
            PrometheusConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy Prometheus stack."""
        try:
            # Parse config
            prometheus_config = PrometheusConfig(**config)

            # Define service definitions that will be created
            service_definitions = [
                {
                    "name": "grafana",
                    "port": 80,
                    "targetPort": 3000,
                    "selector": "app.kubernetes.io/name",
                },
                {
                    "name": "alertmanager",
                    "port": 9093,
                    "targetPort": 9093,
                    "selector": "app.kubernetes.io/name",
                },
                {
                    "name": "prometheus",
                    "port": 9090,
                    "targetPort": 9090,
                    "selector": "app.kubernetes.io/name",
                },
            ]

            # Deploy namespace
            namespace = k8s.core.v1.Namespace(
                f"{self.name}-namespace",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=prometheus_config.namespace,
                    labels=prometheus_config.labels,
                    annotations=prometheus_config.annotations,
                ),
                opts=ResourceOptions(provider=self.provider.provider)
            )

            # Deploy Prometheus stack
            chart_name = "kube-prometheus-stack"
            chart_url = "https://prometheus-community.github.io/helm-charts"

            # Configure Helm values
            helm_values = {}
            if prometheus_config.openunison_enabled:
                helm_values["grafana"] = {
                    "grafana.ini": {
                        "users": {
                            "allow_sign_up": False,
                            "auto_assign_org": True,
                            "auto_assign_org_role": "Admin",
                        },
                        "auth.proxy": {
                            "enabled": True,
                            "header_name": "X-WEBAUTH-USER",
                            "auto_sign_up": True,
                            "headers": "Groups:X-WEBAUTH-GROUPS",
                        },
                    }
                }

            # Deploy Helm release
            release = k8s.helm.v3.Release(
                chart_name,
                k8s.helm.v3.ReleaseArgs(
                    chart=chart_name,
                    version=prometheus_config.version,
                    namespace=prometheus_config.namespace,
                    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                        repo=chart_url
                    ),
                    values=helm_values,
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=namespace,
                    depends_on=[namespace]
                )
            )

            # Create services
            services = self._create_services(prometheus_config, namespace, release)

            # Convert Pulumi Output objects to strings for resource IDs
            resource_ids = [
                f"{self.name}-namespace",  # Use resource names instead of IDs
                f"{chart_name}",
            ]
            resource_ids.extend([f"{self.name}-{svc_def['name']}" for svc_def in service_definitions])

            return ModuleDeploymentResult(
                success=True,
                version=prometheus_config.version or "latest",
                resources=resource_ids,  # Use string resource names
                metadata={
                    "namespace": prometheus_config.namespace,
                    "chart_version": prometheus_config.version,
                    "services": [svc_def["name"] for svc_def in service_definitions]
                }
            )

        except Exception as e:
            log.error(f"Failed to deploy Prometheus: {str(e)}")
            return ModuleDeploymentResult(
                success=False,
                version="",
                errors=[str(e)]
            )

    def _create_services(
        self,
        config: PrometheusConfig,
        namespace: k8s.core.v1.Namespace,
        release: k8s.helm.v3.Release
    ) -> List[k8s.core.v1.Service]:
        """Create Prometheus services."""
        services = []

        service_definitions = [
            {
                "name": "grafana",
                "port": 80,
                "targetPort": 3000,
                "selector": "app.kubernetes.io/name",
            },
            {
                "name": "alertmanager",
                "port": 9093,
                "targetPort": 9093,
                "selector": "app.kubernetes.io/name",
            },
            {
                "name": "prometheus",
                "port": 9090,
                "targetPort": 9090,
                "selector": "app.kubernetes.io/name",
            },
        ]

        for svc_def in service_definitions:
            service = k8s.core.v1.Service(
                f"{self.name}-{svc_def['name']}",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=svc_def["name"],
                    namespace=config.namespace,
                    labels=config.labels,
                    annotations=config.annotations,
                ),
                spec=k8s.core.v1.ServiceSpecArgs(
                    type="ClusterIP",
                    ports=[
                        k8s.core.v1.ServicePortArgs(
                            name="http-web",
                            port=svc_def["port"],
                            protocol="TCP",
                            target_port=svc_def["targetPort"],
                        )
                    ],
                    selector={svc_def["selector"]: svc_def["name"]},
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=namespace,
                    depends_on=[release]
                ),
            )
            services.append(service)

        return services
