# ./modules/kubernetes/resources/workload/service.py
"""
Kubernetes Service resource implementation.
"""
from typing import Dict, Optional
from pulumi import ResourceOptions, CustomTimeouts
import pulumi_kubernetes as k8s


def create_service(
    name: str,
    namespace: str,
    port: int,
    target_port: int,
    selector: Dict[str, str],
    provider: k8s.Provider,
    service_type: str = "ClusterIP",
    protocol: str = "TCP",
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.core.v1.Service:
    """Create a Kubernetes service with standard configuration."""

    return k8s.core.v1.Service(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            type=service_type,
            ports=[
                k8s.core.v1.ServicePortArgs(
                    name="http-web",
                    port=port,
                    protocol=protocol,
                    target_port=target_port,
                )
            ],
            selector=selector,
        ),
        opts=opts
        or ResourceOptions(
            provider=provider,
            custom_timeouts=CustomTimeouts(create="5m", update="5m", delete="10s"),
        ),
    )
