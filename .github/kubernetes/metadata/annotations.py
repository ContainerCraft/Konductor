# ./modules/kubernetes/metadata/annotations.py
"""
Kubernetes metadata annotations module
"""

from typing import Dict, Any, Union
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs


def update_kubernetes_annotations(
    metadata: Union[Dict[str, Any], ObjectMetaArgs], annotations: Dict[str, str]
) -> None:
    """
    Update kubernetes resource annotations.

    Args:
        metadata: Metadata to update.
        annotations: Annotations to update.
    """
    if isinstance(metadata, dict):
        metadata.setdefault("annotations", {}).update(annotations)
    elif isinstance(metadata, ObjectMetaArgs):
        if metadata.annotations is None:
            metadata.annotations = {}
        metadata.annotations.update(annotations)
