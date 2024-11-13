# pulumi/core/resource_helpers.py

"""
Resource Helper Functions Module

This module provides helper functions for creating and managing Pulumi resources,
with proper type safety, resource option handling, and error management.
"""

import os
import tempfile
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any, List, Union, Callable, cast
from pulumi import ResourceOptions, Resource, Output
from pulumi_kubernetes.core.v1 import Namespace, Secret
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, Chart
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.yaml import ConfigFile

from .metadata import get_global_labels, get_global_annotations
from .utils import set_resource_metadata

import importlib
import logging as log
from pulumi_kubernetes import Provider


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
        global_labels = get_global_labels()
        global_annotations = get_global_annotations()
        labels.update(global_labels)
        annotations.update(global_annotations)

        # Create metadata
        metadata = ObjectMetaArgs(
            name=name,
            labels=labels,
            annotations=annotations,
            finalizers=finalizers,
        )

        # Merge resource options
        resource_opts = ResourceOptions.merge(
            ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                parent=parent,
                custom_timeouts=pulumi.CustomTimeouts(
                    create=custom_timeouts.get("create", "5m"),
                    update=custom_timeouts.get("update", "10m"),
                    delete=custom_timeouts.get("delete", "10m"),
                ),
            ),
            opts or ResourceOptions()
        )

        # Create namespace
        return Namespace(
            name,
            metadata=metadata,
            opts=resource_opts,
        )

    except Exception as e:
        raise pulumi.RunError(f"Failed to create namespace '{name}': {str(e)}") from e


def create_custom_resource(
    name: str,
    api_version: str,
    kind: str,
    metadata: Dict[str, Any],
    spec: Dict[str, Any],
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[Resource]] = None,
    parent: Optional[Resource] = None,
) -> CustomResource:
    """
    Creates a Kubernetes CustomResource with global labels and annotations.

    Args:
        name: The name of the custom resource
        api_version: The API version of the custom resource
        kind: The kind of the custom resource
        metadata: The metadata for the custom resource
        spec: The spec for the custom resource
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        depends_on: Resources this custom resource depends on
        parent: Parent resource

    Returns:
        CustomResource: The created CustomResource

    Raises:
        pulumi.RunError: If custom resource creation fails
    """
    try:
        # Initialize defaults
        opts = opts or ResourceOptions()
        depends_on = depends_on or []

        # Get global metadata
        global_labels = get_global_labels()
        global_annotations = get_global_annotations()

        def custom_resource_transform(args: pulumi.ResourceTransformationArgs) -> pulumi.ResourceTransformationResult:
            """Transform resource to include global metadata."""
            props = args.props
            if "metadata" in props:
                set_resource_metadata(
                    props["metadata"],
                    global_labels,
                    global_annotations
                )
            return pulumi.ResourceTransformationResult(props, args.opts)

        # Merge resource options
        resource_opts = ResourceOptions.merge(
            ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                parent=parent,
                transformations=[custom_resource_transform],
            ),
            opts
        )

        # Create custom resource
        return CustomResource(
            resource_name=name,
            api_version=api_version,
            kind=kind,
            metadata=metadata,
            spec=spec,
            opts=resource_opts,
        )

    except Exception as e:
        raise pulumi.RunError(f"Failed to create custom resource '{name}': {str(e)}") from e


def create_helm_release(
    name: str,
    chart: Union[str, Chart],
    values: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
    namespace: Optional[str] = None,
    repository: Optional[str] = None,
    repository_opts: Optional[Dict[str, Any]] = None,
    transformations: Optional[List[Callable[[pulumi.ResourceTransformationArgs], Optional[pulumi.ResourceTransformationResult]]]] = None,
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[Resource]] = None,
    parent: Optional[Resource] = None,
) -> Release:
    """
    Creates a Helm Release with global labels and annotations.

    Args:
        name: The release name
        chart: The chart name or Chart object
        values: The values for the chart
        version: The version of the chart
        namespace: The namespace to install the release into
        repository: The repository URL
        repository_opts: Additional repository options
        transformations: Additional transformations
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        depends_on: Resources this release depends on
        parent: Parent resource

    Returns:
        Release: The created Helm release

    Raises:
        pulumi.RunError: If helm release creation fails
    """
    try:
        # Initialize defaults
        opts = opts or ResourceOptions()
        transformations = transformations or []
        depends_on = depends_on or []
        values = values or {}
        repository_opts = repository_opts or {}

        # Get global metadata
        global_labels = get_global_labels()
        global_annotations = get_global_annotations()

        def helm_resource_transform(args: pulumi.ResourceTransformationArgs) -> pulumi.ResourceTransformationResult:
            """Transform helm resources to include global metadata."""
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

        transformations.append(helm_resource_transform)

        # Merge resource options
        resource_opts = ResourceOptions.merge(
            ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                parent=parent,
                transformations=transformations,
            ),
            opts
        )

        # Create release args
        release_args = ReleaseArgs(
            chart=chart,
            version=version,
            namespace=namespace,
            repository=repository,
            repository_opts=repository_opts,
            values=values,
        )

        return Release(name, release_args, opts=resource_opts)

    except Exception as e:
        raise pulumi.RunError(f"Failed to create helm release '{name}': {str(e)}") from e


def create_secret(
    name: str,
    namespace: str,
    string_data: Dict[str, str],
    opts: Optional[ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[Resource]] = None,
    parent: Optional[Resource] = None,
) -> Secret:
    """
    Creates a Kubernetes Secret with global labels and annotations.

    Args:
        name: The name of the secret
        namespace: The namespace for the secret
        string_data: The secret data as strings
        opts: Pulumi resource options
        k8s_provider: Kubernetes provider
        depends_on: Resources this secret depends on
        parent: Parent resource

    Returns:
        Secret: The created Secret

    Raises:
        pulumi.RunError: If secret creation fails
    """
    try:
        # Initialize defaults
        opts = opts or ResourceOptions()
        depends_on = depends_on or []

        # Get global metadata
        global_labels = get_global_labels()
        global_annotations = get_global_annotations()

        # Create metadata
        metadata = ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=global_labels,
            annotations=global_annotations,
        )

        # Merge resource options
        resource_opts = ResourceOptions.merge(
            ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                parent=parent,
            ),
            opts
        )

        return Secret(
            name,
            metadata=metadata,
            string_data=string_data,
            opts=resource_opts,
        )

    except Exception as e:
        raise pulumi.RunError(f"Failed to create secret '{name}': {str(e)}") from e


def create_config_file(
    name: str,
    file_path: str,
    opts: Optional[ResourceOptions] = None,
    transformations: Optional[List[Callable[[pulumi.ResourceTransformationArgs], Optional[pulumi.ResourceTransformationResult]]]] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[Resource]] = None,
    parent: Optional[Resource] = None,
) -> ConfigFile:
    """
    Creates Kubernetes resources from a YAML config file with global labels and annotations.

    Args:
        name: The resource name
        file_path: The path to the YAML file
        opts: Pulumi resource options
        transformations: Additional transformations
        k8s_provider: Kubernetes provider
        depends_on: Resources these resources depend on
        parent: Parent resource

    Returns:
        ConfigFile: The created resources

    Raises:
        pulumi.RunError: If config file creation fails
    """
    try:
        # Initialize defaults
        opts = opts or ResourceOptions()
        transformations = transformations or []
        depends_on = depends_on or []

        # Get global metadata
        global_labels = get_global_labels()
        global_annotations = get_global_annotations()

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

        transformations.append(config_file_transform)

        # Merge resource options
        resource_opts = ResourceOptions.merge(
            ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                parent=parent,
                transformations=transformations,
            ),
            opts
        )

        return ConfigFile(name, file_path, opts=resource_opts)

    except Exception as e:
        raise pulumi.RunError(f"Failed to create config file '{name}': {str(e)}") from e


def create_aws_resource(
    name: str,
    resource_type: str,
    args: Dict[str, Any],
    opts: Optional[ResourceOptions] = None,
    provider: Optional[Provider] = None
) -> pulumi.Resource:
    """Create AWS resource with proper error handling."""
    try:
        # Ensure required fields
        if not name or not resource_type:
            raise ValueError("Name and resource_type are required")

        # Get resource class
        module = importlib.import_module("pulumi_aws")
        resource_class = getattr(module, resource_type)

        # Create resource
        return resource_class(
            name,
            **args,
            opts=ResourceOptions.merge(
                ResourceOptions(provider=provider),
                opts or ResourceOptions()
            )
        )

    except Exception as e:
        log.error(f"Failed to create AWS resource {name}: {str(e)}")
        raise
