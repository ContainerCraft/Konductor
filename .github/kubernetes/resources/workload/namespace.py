# ./modules/kubernetes/resources/workload/namespace.py
from typing import Dict, Optional
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s


def create_namespace(
    name: str,
    provider: k8s.Provider,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.core.v1.Namespace:
    """Create a Kubernetes namespace with metadata."""

    return k8s.core.v1.Namespace(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            labels=labels or {},
            annotations=annotations or {},
        ),
        opts=opts or ResourceOptions(provider=provider),
    )
