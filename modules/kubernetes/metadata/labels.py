# ./modules/kubernetes/metadata/labels.py
"""
Kubernetes metadata labels module
"""

from typing import Dict, Any, Union
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs


def update_kubernetes_labels(
    metadata: Union[Dict[str, Any], ObjectMetaArgs], labels: Dict[str, str]
) -> None:
    """
    Update kubernetes resource labels.

    Args:
        metadata: Metadata to update.
        labels: Labels to update.
    """
    if isinstance(metadata, dict):
        metadata.setdefault("labels", {}).update(labels)
    elif isinstance(metadata, ObjectMetaArgs):
        if metadata.labels is None:
            metadata.labels = {}
        metadata.labels.update(labels)
