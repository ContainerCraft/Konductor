# pulumi/core/utils.py

"""
Utility Functions Module

This module provides generic, reusable utility functions for Pulumi resource management.
Includes resource transformations, Helm interactions, and infrastructure utilities.
"""

import re
import os
import tempfile
import json
from typing import Optional, Dict, Any, List, Union, Callable, TypeVar, cast
from pulumi import Output
from pulumi.output import Output as OutputType
import requests
import yaml
import logging
from packaging.version import parse as parse_version, InvalidVersion, Version
from pulumi import ResourceOptions, Resource, ResourceTransformationArgs, ResourceTransformationResult, runtime
import pulumi_kubernetes as k8s
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
import time
import pulumi
from pulumi import log

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Type variables for generic functions
T = TypeVar('T')
MetadataType = Union[Dict[str, Any], ObjectMetaArgs, Output[Dict[str, Any]]]

def set_resource_metadata(
    metadata: MetadataType,
    global_labels: Dict[str, str],
    global_annotations: Dict[str, str]
) -> MetadataType:
    """
    Updates resource metadata with global labels and annotations.
    Handles both dict and ObjectMetaArgs metadata types.

    Args:
        metadata: Resource metadata to update
        global_labels: Global labels to apply
        global_annotations: Global annotations to apply

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
            return metadata_output.apply(lambda m: {
                **m,
                "labels": {**(m.get("labels", {})), **global_labels},
                "annotations": {**(m.get("annotations", {})), **global_annotations}
            })
        else:
            raise TypeError(f"Unsupported metadata type: {type(metadata)}")
    except Exception as e:
        logging.error(f"Failed to update resource metadata: {str(e)}")
        raise


def generate_global_transformations(
    global_labels: Dict[str, str],
    global_annotations: Dict[str, str]
) -> None:
    """
    Registers global transformations for all Pulumi resources.
    Ensures consistent metadata across all resources.

    Args:
        global_labels: Global labels to apply
        global_annotations: Global annotations to apply
    """
    def global_transform(
        args: pulumi.ResourceTransformationArgs,
    ) -> pulumi.ResourceTransformationResult:
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
                set_resource_metadata(props["metadata"], global_labels, global_annotations)
            elif "spec" in props and isinstance(props["spec"], dict):
                if "metadata" in props["spec"]:
                    set_resource_metadata(
                        props["spec"]["metadata"],
                        global_labels,
                        global_annotations
                    )

            return ResourceTransformationResult(props, args.opts)
        except Exception as e:
            logging.error(f"Error in global transform: {str(e)}")
            return ResourceTransformationResult(props, args.opts)

    pulumi.runtime.register_stack_transformation(global_transform)


def get_latest_helm_chart_version(
    repo_url: str,
    chart_name: str,
    timeout: int = 30,
    verify_ssl: bool = True,
    max_retries: int = 3,
) -> str:
    """
    Fetches the latest stable version of a Helm chart.
    Includes retry logic and proper error handling.

    Args:
        repo_url: The base URL of the Helm repository
        chart_name: The name of the Helm chart
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        max_retries: Number of retry attempts

    Returns:
        str: The latest stable version or error message

    Raises:
        requests.RequestException: If the request fails
        yaml.YAMLError: If parsing the index fails
    """
    for attempt in range(max_retries):
        try:
            index_url = repo_url.rstrip("/") + "/index.yaml"
            logging.info(f"Fetching Helm repository index from URL: {index_url}")

            response = requests.get(
                index_url,
                timeout=timeout,
                verify=verify_ssl
            )
            response.raise_for_status()

            index = yaml.safe_load(response.content)

            if chart_name not in index.get("entries", {}):
                logging.warning(f"No chart named '{chart_name}' found in repository")
                return "Chart not found"

            chart_versions = index["entries"][chart_name]
            stable_versions = [
                v for v in chart_versions
                if is_stable_version(v["version"])
            ]

            if not stable_versions:
                logging.warning(f"No stable versions found for chart '{chart_name}'")
                return "No stable versions found"

            latest_chart = max(
                stable_versions,
                key=lambda x: parse_version(x["version"])
            )

            version = latest_chart["version"].lstrip("v")
            logging.info(f"Found latest version {version} for chart {chart_name}")
            return version

        except (requests.RequestException, yaml.YAMLError) as e:
            if attempt == max_retries - 1:
                raise
            logging.warning(f"Attempt {attempt + 1} failed, retrying: {str(e)}")
            time.sleep(2 ** attempt)

    return "Failed to fetch chart version after all retries"


def is_stable_version(version_str: str) -> bool:
    """
    Determines if a version string represents a stable release.
    Handles various version formats and edge cases.

    Args:
        version_str: The version string to check

    Returns:
        bool: True if the version is stable
    """
    try:
        version = parse_version(version_str)
        return (
            isinstance(version, Version) and
            not version.is_prerelease and
            not version.is_devrelease and
            not version.is_postrelease
        )
    except InvalidVersion:
        return False


def extract_repo_name(remote_url: str) -> str:
    """
    Extracts the repository name from a Git remote URL.
    Handles various Git URL formats.

    Args:
        remote_url: The Git remote URL

    Returns:
        str: The repository name or original URL if parsing fails
    """
    try:
        # Handle SSH URLs
        if remote_url.startswith("git@"):
            parts = remote_url.split(":")
            if len(parts) == 2:
                return parts[1].rstrip(".git")

        # Handle HTTPS URLs
        match = re.search(r"[:/]([^/:]+/[^/\.]+)(\.git)?$", remote_url)
        if match:
            return match.group(1)

        return remote_url
    except Exception as e:
        logging.warning(f"Error extracting repo name from {remote_url}: {str(e)}")
        return remote_url


def wait_for_crds(
    crd_names: List[str],
    k8s_provider: k8s.Provider,
    depends_on: List[Resource],
    parent: Resource,
    timeout: int = 300
) -> List[Resource]:
    """
    Waits for CRDs to be present and ensures dependencies.
    Includes timeout and proper error handling.

    Args:
        crd_names: List of CRD names to wait for
        k8s_provider: The Kubernetes provider
        depends_on: List of dependencies
        parent: The parent resource
        timeout: Timeout in seconds

    Returns:
        List[Resource]: The CRD resources or dummy CRDs during preview

    Raises:
        TimeoutError: If CRDs don't become ready within timeout
        pulumi.ResourceError: If CRD creation fails
    """
    crds: List[Resource] = []

    for crd_name in crd_names:
        try:
            crd = k8s.apiextensions.v1.CustomResourceDefinition.get(
                resource_name=f"crd-{crd_name}",
                id=crd_name,
                opts=ResourceOptions(
                    provider=k8s_provider,
                    depends_on=depends_on,
                    parent=parent,
                    custom_timeouts=pulumi.CustomTimeouts(
                        create=f"{timeout}s",
                        delete="60s"
                    ),
                ),
            )
            crds.append(crd)
        except Exception:
            if pulumi.runtime.is_dry_run():
                logging.info(f"CRD {crd_name} not found, creating dummy CRD")
                dummy_crd = create_dummy_crd(
                    crd_name,
                    k8s_provider,
                    depends_on,
                    parent
                )
                if dummy_crd:
                    crds.append(dummy_crd)

    return crds


def create_dummy_crd(
    crd_name: str,
    k8s_provider: k8s.Provider,
    depends_on: List[Resource],
    parent: Resource
) -> Optional[k8s.yaml.ConfigFile]:
    """
    Creates a dummy CRD for preview runs.
    Ensures proper cleanup of temporary files.

    Args:
        crd_name: The name of the CRD
        k8s_provider: The Kubernetes provider
        depends_on: List of dependencies
        parent: The parent resource

    Returns:
        Optional[k8s.yaml.ConfigFile]: The dummy CRD resource
    """
    parts = crd_name.split(".")
    plural = parts[0]
    group = ".".join(parts[1:])
    kind = "".join(word.title() for word in plural.split("_"))

    dummy_crd_yaml = f"""
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: {plural}.{group}
spec:
  group: {group}
  names:
    plural: {plural}
    singular: {plural.lower()}
    kind: {kind}
    shortNames: [{plural[:3].lower()}]
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              x-kubernetes-preserve-unknown-fields: true
    """

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False
        ) as temp_file:
            temp_file.write(dummy_crd_yaml)
            temp_file_path = temp_file.name

        return k8s.yaml.ConfigFile(
            f"dummy-crd-{crd_name}",
            file=temp_file_path,
            opts=ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                parent=parent,
            ),
        )
    except Exception as e:
        logging.error(f"Error creating dummy CRD: {str(e)}")
        return None
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
