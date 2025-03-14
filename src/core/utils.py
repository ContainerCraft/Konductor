# ./modules/core/utils.py

"""
Utility Functions Module

This module provides a collection of generic and reusable utility functions
designed to assist with Pulumi resource management. These utilities include
functions for resource transformations, Helm interactions, and other
infrastructure-related operations.
"""

from typing import Any, Dict, Union
from pulumi import (
    ResourceTransformationArgs,
    ResourceTransformationResult,
    Resource,
    log,
    runtime,
)

from .types import CommonMetadataFields


def set_resource_metadata(
    metadata: Dict[str, Any],
    global_tags: Dict[str, str],
    global_labels: Dict[str, str],
    global_annotations: Dict[str, str],
) -> Dict[str, Any]:
    """
    Update the metadata of a resource with global labels and annotations.

    This function modifies the provided metadata dictionary by adding or updating
    its 'tags', 'labels', and 'annotations' fields with the specified global labels
    and annotations. This is a base implementation and can be extended for
    provider-specific requirements.

    Global tags, labels, and annotations are applied to all resources in the stack
    by merging the global metadata with module and submodule specific metadata.

    Provider-specific implementations should conform with provider module
    encapsulation.

    Args:
        metadata: The metadata dictionary to be updated.
        global_tags: A dictionary of global tags to apply.
        global_labels: A dictionary of global labels to apply.
        global_annotations: A dictionary of global annotations to apply.

    Returns:
        Dict[str, Any]: The updated metadata dictionary with applied labels and
        annotations.
    """
    if isinstance(metadata, dict):
        metadata.setdefault("tags", {}).update(global_tags)
        metadata.setdefault("labels", {}).update(global_labels)
        metadata.setdefault("annotations", {}).update(global_annotations)
    return metadata


def generate_global_transformations(
    global_tags: Dict[str, str],
    global_labels: Dict[str, str],
    global_annotations: Dict[str, str],
) -> None:
    """
    Register global transformations to apply consistent metadata across all Pulumi
    resources.

    This function sets up a transformation that will be applied to every Pulumi
    resource in the stack. It ensures that each resource has the specified global
    labels, annotations, and tags in its metadata, promoting uniformity and ease
    of management.

    Args:
        global_tags: A dictionary of global tags to apply to all resources.
        global_labels: A dictionary of global labels to apply to all resources.
        global_annotations: A dictionary of global annotations to apply.
    """

    def global_transform(
        args: ResourceTransformationArgs,
    ) -> ResourceTransformationResult:
        """
        Apply a global transformation to a Pulumi resource for consistent metadata.

        This function is called for each resource during the transformation
        process. It checks if the resource has a 'metadata' or 'spec.metadata'
        field and updates it with the provided global labels and annotations.

        Args:
            args: The arguments containing resource properties and options.

        Returns:
            ResourceTransformationResult: The transformed resource properties.
        """
        props = args.props

        try:
            if "metadata" in props:
                set_resource_metadata(
                    props["metadata"],
                    global_tags,
                    global_labels,
                    global_annotations,
                )
            elif "spec" in props and isinstance(props["spec"], dict):
                if "metadata" in props["spec"]:
                    set_resource_metadata(
                        props["spec"]["metadata"],
                        global_tags,
                        global_labels,
                        global_annotations,
                    )

            return ResourceTransformationResult(props, args.opts)
        except Exception as e:
            log.error(f"Error in global transform: {str(e)}")
            return ResourceTransformationResult(props, args.opts)

    runtime.register_stack_transformation(global_transform)


def apply_metadata(
    resource: Union[Resource, Any],
    metadata: CommonMetadataFields,
) -> None:
    """
    Apply metadata to a resource if it supports metadata fields.

    This function applies tags, labels, and annotations from a CommonMetadataFields
    object to a resource that supports these fields. It's a convenience wrapper
    around the individual apply functions.

    Args:
        resource: The resource to which metadata should be applied.
        metadata: CommonMetadataFields containing tags, labels, and annotations.
    """
    apply_tags(resource, metadata.tags)
    apply_labels(resource, metadata.labels)
    apply_annotations(resource, metadata.annotations)


def apply_tags(resource: Union[Resource, Any], tags: Dict[str, str]) -> None:
    """
    Apply tags to a resource if it supports tagging.

    This function checks if the given resource has a 'tags' attribute and, if so,
    updates it with the provided tags. This is useful for adding metadata to
    resources that support tagging, such as cloud infrastructure components.

    Args:
        resource: The resource to which tags should be applied.
        tags: A dictionary of tags to apply to the resource.
    """
    if hasattr(resource, "tags"):
        resource.tags.update(tags)


def apply_labels(resource: Union[Resource, Any], labels: Dict[str, str]) -> None:
    """
    Apply labels to a resource if it supports labeling.

    This function checks if the given resource has a 'labels' attribute and,
    if so, updates it with the provided labels. This is commonly used with
    Kubernetes resources and other systems that support labeling.

    Args:
        resource: The resource to which labels should be applied.
        labels: A dictionary of labels to apply to the resource.
    """
    if hasattr(resource, "labels"):
        resource.labels.update(labels)


def apply_annotations(
    resource: Union[Resource, Any],
    annotations: Dict[str, str]
) -> None:
    """
    Apply annotations to a resource if it supports annotations.

    This function checks if the given resource has an 'annotations' attribute and,
    if so, updates it with the provided annotations. This is commonly used with
    Kubernetes resources and other systems that support annotations.

    Args:
        resource: The resource to which annotations should be applied.
        annotations: A dictionary of annotations to apply to the resource.
    """
    if hasattr(resource, "annotations"):
        resource.annotations.update(annotations)
