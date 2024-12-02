# ../konductor/modules/core/utils.py
"""
Utility Functions Module

This module provides generic, reusable utility functions for Pulumi resource management.
Includes resource transformations, Helm interactions, and infrastructure utilities.
"""

from typing import Any, Dict, TypeVar, Union, cast

from pulumi import (
    Output,
    ResourceTransformationArgs,
    ResourceTransformationResult,
    log,
    runtime,
)
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

# Type variables for generic functions
T = TypeVar("T")
MetadataType = Union[Dict[str, Any], ObjectMetaArgs, Output[Dict[str, Any]]]


def set_resource_metadata(
    metadata: MetadataType,
    global_labels: Dict[str, str],
    global_annotations: Dict[str, str],
) -> MetadataType:
    """
    Updates resource metadata with global labels and annotations.

    Args:
        metadata: Resource metadata to update
        global_labels: Global labels to apply
        global_annotations: Global annotations to apply

    Returns:
        MetadataType: Updated metadata

    Raises:
        TypeError: If metadata is of an unsupported type
    """
    try:
        if isinstance(metadata, (dict, ObjectMetaArgs)):
            if isinstance(metadata, dict):
                metadata.setdefault("labels", {}).update(global_labels)
                metadata.setdefault("annotations", {}).update(global_annotations)
            else:
                if metadata.labels is None:
                    metadata.labels = {}
                metadata.labels.update(global_labels)
                if metadata.annotations is None:
                    metadata.annotations = {}
                metadata.annotations.update(global_annotations)
        elif isinstance(metadata, Output):
            metadata_output = cast(Output[Dict[str, Any]], metadata)
            return metadata_output.apply(
                lambda m: {
                    **m,
                    "labels": {**(m.get("labels", {})), **global_labels},
                    "annotations": {**(m.get("annotations", {})), **global_annotations},
                }
            )
        else:
            raise TypeError(f"Unsupported metadata type: {type(metadata)}")
    except Exception as e:
        log.error(f"Failed to update resource metadata: {str(e)}")
        raise

    return metadata


def generate_global_transformations(
    global_labels: Dict[str, str], global_annotations: Dict[str, str]
) -> None:
    """
    Registers global transformations for all Pulumi resources.
    Ensures consistent metadata across all resources.

    Args:
        global_labels: Global labels to apply
        global_annotations: Global annotations to apply
    """

    def global_transform(
        args: ResourceTransformationArgs,
    ) -> ResourceTransformationResult:
        """
        Global transformation function for Pulumi resources.
        Applies metadata consistently across all resources.

        Args:
            args: Resource transformation arguments

        Returns:
            ResourceTransformationResult: Transformed resource properties
        """
        props = args.props

        try:
            if "metadata" in props:
                set_resource_metadata(
                    props["metadata"], global_labels, global_annotations
                )
            elif "spec" in props and isinstance(props["spec"], dict):
                if "metadata" in props["spec"]:
                    set_resource_metadata(
                        props["spec"]["metadata"], global_labels, global_annotations
                    )

            return ResourceTransformationResult(props, args.opts)
        except Exception as e:
            log.error(f"Error in global transform: {str(e)}")
            return ResourceTransformationResult(props, args.opts)

    runtime.register_stack_transformation(global_transform)


def apply_tags(resource, tags: dict):
    if hasattr(resource, "tags"):
        resource.tags.update(tags)
