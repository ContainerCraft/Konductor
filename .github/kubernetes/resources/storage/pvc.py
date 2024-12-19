# ./modules/kubernetes/resources/storage/pvc.py
from typing import Optional
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s


def create_persistent_volume_claim(
    name: str,
    namespace: str,
    storage_class: str,
    storage_size: str,
    provider: k8s.Provider,
    access_modes: Optional[list[str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.core.v1.PersistentVolumeClaim:
    """Create a PersistentVolumeClaim with standard configuration."""

    return k8s.core.v1.PersistentVolumeClaim(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(name=name, namespace=namespace),
        spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
            access_modes=access_modes or ["ReadWriteOnce"],
            resources=k8s.core.v1.ResourceRequirementsArgs(requests={"storage": storage_size}),
            storage_class_name=storage_class,
        ),
        opts=opts or ResourceOptions(provider=provider),
    )
