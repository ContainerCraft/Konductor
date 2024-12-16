# ./modules/kubernetes/components/prometheus/deployment.py
"""
Prometheus component deployment implementation.

TODO:
- Migrate, add, and complete Prometheus component deployment logic implementation.
"""
from typing import Dict, Any, List
from pulumi import log, ResourceOptions, CustomTimeouts
import pulumi_kubernetes as k8s

from ...resources.workload.namespace import create_namespace
from ...resources.workload.service import create_service
from ...resources.helm.chart import create_helm_chart
from ..base import KubernetesComponent
from .types import PrometheusConfig
from modules.core.interfaces import ModuleDeploymentResult


class PrometheusComponent(KubernetesComponent):
    """Prometheus component implementation."""

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

            # Define service definitions
            service_definitions = [
                {
                    "name": "grafana",
                    "port": 80,
                    "target_port": 3000,
                    "selector": "app.kubernetes.io/name",
                },
                {
                    "name": "alertmanager",
                    "port": 9093,
                    "target_port": 9093,
                    "selector": "app.kubernetes.io/name",
                },
                {
                    "name": "prometheus",
                    "port": 9090,
                    "target_port": 9090,
                    "selector": "app.kubernetes.io/name",
                },
            ]

            # Deploy namespace
            namespace = create_namespace(
                f"{self.name}-namespace",
                self.provider.provider,
                labels=prometheus_config.labels,
                annotations=prometheus_config.annotations,
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
            release = create_helm_chart(
                chart_name,
                chart_url,
                prometheus_config.namespace,
                prometheus_config.version,
                helm_values,
                self.provider.provider,
                opts=ResourceOptions(provider=self.provider.provider, parent=namespace, depends_on=[namespace]),
            )

            # Create services
            services = []
            for svc_def in service_definitions:
                service = create_service(
                    f"{self.name}-{svc_def['name']}",
                    prometheus_config.namespace,
                    svc_def["port"],
                    svc_def["target_port"],
                    {svc_def["selector"]: svc_def["name"]},
                    self.provider.provider,
                    labels=prometheus_config.labels,
                    annotations=prometheus_config.annotations,
                    opts=ResourceOptions(provider=self.provider.provider, parent=namespace, depends_on=[release]),
                )
                services.append(service)

            # Convert Pulumi Output objects to strings for resource IDs
            resource_ids = [
                f"{self.name}-namespace",
                chart_name,
            ]
            resource_ids.extend([f"{self.name}-{svc_def['name']}" for svc_def in service_definitions])

            return ModuleDeploymentResult(
                success=True,
                version=prometheus_config.version or "latest",
                resources=resource_ids,
                metadata={
                    "namespace": prometheus_config.namespace,
                    "chart_version": prometheus_config.version,
                    "services": [svc_def["name"] for svc_def in service_definitions],
                },
            )

        except Exception as e:
            log.error(f"Failed to deploy Prometheus: {str(e)}")
            return ModuleDeploymentResult(success=False, version="", errors=[str(e)])
