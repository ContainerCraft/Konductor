# ./modules/core/resource_helpers.py

"""
Resource Helper Functions Module

This module provides helper functions for creating and managing Pulumi resources,
with proper type safety, resource option handling, and error management.
"""

import importlib
import logging as log
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any, List
from pulumi import ResourceOptions, Resource, Output
from pulumi_kubernetes.core.v1 import Namespace, Secret
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.yaml import ConfigFile

from .metadata import MetadataSingleton
from .utils import set_resource_metadata


def create_namespace(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    finalizers: Optional[List[str]] = None,
    custom_timeouts: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    parent: Optional[Resource] = None,
    depends_on: Optional[List[Resource]] = None,
) -> Namespace:
    """
    Creates a Kubernetes Namespace with global labels and annotations.

    Args:
        name: The name of the namespace
        labels: Additional labels to apply
        annotations: Additional annotations to apply
        finalizers: Finalizers for the namespace
        custom_timeouts: Custom timeouts for resource operations
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        parent: Parent resource
        depends_on: Resources this resource depends on

    Returns:
        Namespace: The created Namespace resource

    Raises:
        pulumi.RunError: If namespace creation fails
    """
    try:
        # Initialize default values
        labels = labels or {}
        annotations = annotations or {}
        custom_timeouts = custom_timeouts or {
            "create": "5m",
            "update": "10m",
            "delete": "10m"
        }
        depends_on = depends_on or []

        # Merge global metadata
        metadata = MetadataSingleton()
        labels.update(metadata.global_labels)
        annotations.update(metadata.global_annotations)

        # Create metadata
        metadata_args = ObjectMetaArgs(
            name=name,
            labels=labels,
            annotations=annotations,
            finalizers=finalizers
        )

        # Create the namespace
        return Namespace(
            name,
            metadata=metadata_args,
            opts=ResourceOptions(
                provider=k8s_provider,
                parent=parent,
                depends_on=depends_on,
                custom_timeouts=custom_timeouts,
                merge=opts
            )
        )
    except Exception as e:
        log.error(f"Failed to create namespace '{name}': {str(e)}")
        raise pulumi.RunError(f"Failed to create namespace '{name}': {str(e)}") from e


def create_custom_resource(
    name: str,
    api_version: str,
    kind: str,
    metadata: Dict[str, Any],
    spec: Dict[str, Any],
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    parent: Optional[Resource] = None,
    depends_on: Optional[List[Resource]] = None,
) -> CustomResource:
    """
    Creates a Kubernetes Custom Resource with global labels and annotations.

    Args:
        name: The name of the custom resource
        api_version: API version of the custom resource
        kind: Kind of the custom resource
        metadata: Metadata for the custom resource
        spec: Specification for the custom resource
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        parent: Parent resource
        depends_on: Resources this resource depends on

    Returns:
        CustomResource: The created Custom Resource

    Raises:
        pulumi.RunError: If custom resource creation fails
    """
    try:
        # Initialize default values
        metadata = metadata or {}
        depends_on = depends_on or []

        # Merge global metadata
        metadata_singleton = MetadataSingleton()
        metadata.setdefault("labels", {}).update(metadata_singleton.global_labels)
        metadata.setdefault("annotations", {}).update(metadata_singleton.global_annotations)

        # Create the custom resource
        return CustomResource(
            name,
            api_version=api_version,
            kind=kind,
            metadata=metadata,
            spec=spec,
            opts=ResourceOptions(
                provider=k8s_provider,
                parent=parent,
                depends_on=depends_on,
                merge=opts
            )
        )
    except Exception as e:
        log.error(f"Failed to create custom resource '{name}': {str(e)}")
        raise pulumi.RunError(f"Failed to create custom resource '{name}': {str(e)}") from e


def create_helm_release(
    name: str,
    chart: str,
    namespace: str,
    values: Optional[Dict[str, Any]] = None,
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    parent: Optional[Resource] = None,
    depends_on: Optional[List[Resource]] = None,
) -> Release:
    """
    Creates a Helm Release with global labels and annotations.

    Args:
        name: The name of the Helm release
        chart: The chart to deploy
        namespace: The namespace to deploy the chart in
        values: Values to override in the chart
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        parent: Parent resource
        depends_on: Resources this resource depends on

    Returns:
        Release: The created Helm Release

    Raises:
        pulumi.RunError: If Helm release creation fails
    """
    try:
        # Initialize default values
        values = values or {}
        depends_on = depends_on or []

        # Merge global metadata
        metadata_singleton = MetadataSingleton()
        values.setdefault("metadata", {}).setdefault("labels", {}).update(metadata_singleton.global_labels)
        values.setdefault("metadata", {}).setdefault("annotations", {}).update(metadata_singleton.global_annotations)

        # Create the Helm release
        return Release(
            name,
            ReleaseArgs(
                chart=chart,
                namespace=namespace,
                values=values
            ),
            opts=ResourceOptions(
                provider=k8s_provider,
                parent=parent,
                depends_on=depends_on,
                merge=opts
            )
        )
    except Exception as e:
        log.error(f"Failed to create Helm release '{name}': {str(e)}")
        raise pulumi.RunError(f"Failed to create Helm release '{name}': {str(e)}") from e


def create_secret(
    name: str,
    data: Dict[str, str],
    namespace: str,
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    parent: Optional[Resource] = None,
    depends_on: Optional[List[Resource]] = None,
) -> Secret:
    """
    Creates a Kubernetes Secret with global labels and annotations.

    Args:
        name: The name of the secret
        data: The data to store in the secret
        namespace: The namespace to create the secret in
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        parent: Parent resource
        depends_on: Resources this resource depends on

    Returns:
        Secret: The created Secret

    Raises:
        pulumi.RunError: If secret creation fails
    """
    try:
        # Initialize default values
        depends_on = depends_on or []

        # Merge global metadata
        metadata_singleton = MetadataSingleton()
        metadata = ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=metadata_singleton.global_labels,
            annotations=metadata_singleton.global_annotations
        )

        # Create the secret
        return Secret(
            name,
            metadata=metadata,
            data=data,
            opts=ResourceOptions(
                provider=k8s_provider,
                parent=parent,
                depends_on=depends_on,
                merge=opts
            )
        )
    except Exception as e:
        log.error(f"Failed to create secret '{name}': {str(e)}")
        raise pulumi.RunError(f"Failed to create secret '{name}': {str(e)}") from e


def create_config_file(
    name: str,
    file_path: str,
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    parent: Optional[Resource] = None,
    depends_on: Optional[List[Resource]] = None,
) -> ConfigFile:
    """
    Creates resources from a Kubernetes YAML configuration file with global labels and annotations.

    Args:
        name: The name of the config file resource
        file_path: The path to the YAML configuration file
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        parent: Parent resource
        depends_on: Resources this resource depends on

    Returns:
        ConfigFile: The created resources

    Raises:
        pulumi.RunError: If config file creation fails
    """
    try:
        # Initialize defaults
        opts = opts or ResourceOptions()
        depends_on = depends_on or []

        # Get global metadata
        metadata_singleton = MetadataSingleton()
        global_labels = metadata_singleton.global_labels
        global_annotations = metadata_singleton.global_annotations

        def config_file_transform(args: pulumi.ResourceTransformationArgs) -> pulumi.ResourceTransformationResult:
            """Transform config file resources to include global metadata."""
            props = args.props
            if "metadata" in props:
                set_resource_metadata(
                    props["metadata"],
                    global_labels,
                    global_annotations
                )
            elif "spec" in props and isinstance(props["spec"], dict):
                if "metadata" in props["spec"]:
                    set_resource_metadata(
                        props["spec"]["metadata"],
                        global_labels,
                        global_annotations
                    )
            return pulumi.ResourceTransformationResult(props, args.opts)

        # Merge resource options
        resource_opts = ResourceOptions.merge(
            ResourceOptions(
                provider=k8s_provider,
                parent=parent,
                depends_on=depends_on,
                transformations=[config_file_transform],
            ),
            opts
        )

        return ConfigFile(name, file_path, opts=resource_opts)

    except Exception as e:
        log.error(f"Failed to create config file '{name}': {str(e)}")
        raise pulumi.RunError(f"Failed to create config file '{name}': {str(e)}") from e
