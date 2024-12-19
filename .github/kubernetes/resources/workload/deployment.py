# ./modules/kubernetes/resources/workload/deployment.py
"""
Kubernetes Deployment resource implementations.
"""
from typing import Dict, Any, Optional, List, Union
from pulumi import ResourceOptions, Output
import pulumi_kubernetes as k8s


def create_deployment(
    name: str,
    namespace: str,
    container_image: str,
    provider: k8s.Provider,
    replicas: int = 1,
    container_ports: Optional[List[Dict[str, Any]]] = None,
    env_vars: Optional[List[Dict[str, Any]]] = None,
    volume_mounts: Optional[List[Dict[str, Any]]] = None,
    volumes: Optional[List[Dict[str, Any]]] = None,
    resources: Optional[Dict[str, Dict[str, str]]] = None,
    service_account_name: Optional[str] = None,
    node_selector: Optional[Dict[str, str]] = None,
    tolerations: Optional[List[Dict[str, Any]]] = None,
    affinity: Optional[Dict[str, Any]] = None,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    pod_labels: Optional[Dict[str, str]] = None,
    pod_annotations: Optional[Dict[str, str]] = None,
    security_context: Optional[Dict[str, Any]] = None,
    container_args: Optional[List[str]] = None,
    container_command: Optional[List[str]] = None,
    image_pull_secrets: Optional[List[Dict[str, str]]] = None,
    strategy: Optional[Dict[str, Any]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.apps.v1.Deployment:
    """
    Create a Kubernetes Deployment with standard configuration.

    Args:
        name: Name of the deployment
        namespace: Namespace for the deployment
        container_image: Container image to deploy
        provider: Kubernetes provider
        replicas: Number of replicas (default: 1)
        container_ports: Optional list of container ports
        env_vars: Optional list of environment variables
        volume_mounts: Optional list of volume mounts
        volumes: Optional list of volumes
        resources: Optional resource requirements
        service_account_name: Optional service account name
        node_selector: Optional node selector
        tolerations: Optional tolerations
        affinity: Optional affinity rules
        labels: Optional deployment labels
        annotations: Optional deployment annotations
        pod_labels: Optional pod labels
        pod_annotations: Optional pod annotations
        security_context: Optional security context
        container_args: Optional container arguments
        container_command: Optional container command
        image_pull_secrets: Optional image pull secrets
        strategy: Optional deployment strategy
        opts: Optional resource options

    Returns:
        k8s.apps.v1.Deployment: Created Deployment resource
    """
    # Prepare container spec
    container = {
        "name": name,
        "image": container_image,
    }

    if container_ports:
        container["ports"] = container_ports
    if env_vars:
        container["env"] = env_vars
    if volume_mounts:
        container["volumeMounts"] = volume_mounts
    if resources:
        container["resources"] = resources
    if container_args:
        container["args"] = container_args
    if container_command:
        container["command"] = container_command

    # Prepare pod template spec
    template_spec = {
        "containers": [container],
    }

    if volumes:
        template_spec["volumes"] = volumes
    if service_account_name:
        template_spec["serviceAccountName"] = service_account_name
    if node_selector:
        template_spec["nodeSelector"] = node_selector
    if tolerations:
        template_spec["tolerations"] = tolerations
    if affinity:
        template_spec["affinity"] = affinity
    if security_context:
        template_spec["securityContext"] = security_context
    if image_pull_secrets:
        template_spec["imagePullSecrets"] = image_pull_secrets

    # Create deployment
    return k8s.apps.v1.Deployment(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            replicas=replicas,
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=pod_labels or {"app": name}),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels=pod_labels or {"app": name},
                    annotations=pod_annotations or {},
                ),
                spec=template_spec,
            ),
            strategy=strategy,
        ),
        opts=opts or ResourceOptions(provider=provider),
    )


def create_stateful_set(
    name: str,
    namespace: str,
    container_image: str,
    provider: k8s.Provider,
    storage_class_name: str,
    storage_size: str,
    replicas: int = 1,
    container_ports: Optional[List[Dict[str, Any]]] = None,
    env_vars: Optional[List[Dict[str, Any]]] = None,
    volume_mounts: Optional[List[Dict[str, Any]]] = None,
    additional_volumes: Optional[List[Dict[str, Any]]] = None,
    resources: Optional[Dict[str, Dict[str, str]]] = None,
    service_account_name: Optional[str] = None,
    node_selector: Optional[Dict[str, str]] = None,
    tolerations: Optional[List[Dict[str, Any]]] = None,
    affinity: Optional[Dict[str, Any]] = None,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    pod_labels: Optional[Dict[str, str]] = None,
    pod_annotations: Optional[Dict[str, str]] = None,
    security_context: Optional[Dict[str, Any]] = None,
    container_args: Optional[List[str]] = None,
    container_command: Optional[List[str]] = None,
    image_pull_secrets: Optional[List[Dict[str, str]]] = None,
    update_strategy: Optional[Dict[str, Any]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.apps.v1.StatefulSet:
    """
    Create a Kubernetes StatefulSet with standard configuration.

    Args:
        name: Name of the stateful set
        namespace: Namespace for the stateful set
        container_image: Container image to deploy
        provider: Kubernetes provider
        storage_class_name: Storage class for PVCs
        storage_size: Storage size for PVCs
        replicas: Number of replicas (default: 1)
        container_ports: Optional list of container ports
        env_vars: Optional list of environment variables
        volume_mounts: Optional list of volume mounts
        additional_volumes: Optional list of additional volumes
        resources: Optional resource requirements
        service_account_name: Optional service account name
        node_selector: Optional node selector
        tolerations: Optional tolerations
        affinity: Optional affinity rules
        labels: Optional stateful set labels
        annotations: Optional stateful set annotations
        pod_labels: Optional pod labels
        pod_annotations: Optional pod annotations
        security_context: Optional security context
        container_args: Optional container arguments
        container_command: Optional container command
        image_pull_secrets: Optional image pull secrets
        update_strategy: Optional update strategy
        opts: Optional resource options

    Returns:
        k8s.apps.v1.StatefulSet: Created StatefulSet resource
    """
    # Prepare container spec
    container = {
        "name": name,
        "image": container_image,
    }

    if container_ports:
        container["ports"] = container_ports
    if env_vars:
        container["env"] = env_vars
    if volume_mounts:
        container["volumeMounts"] = volume_mounts
    if resources:
        container["resources"] = resources
    if container_args:
        container["args"] = container_args
    if container_command:
        container["command"] = container_command

    # Prepare volumes
    volumes = additional_volumes or []
    volume_claim_templates = [
        k8s.core.v1.PersistentVolumeClaimArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"{name}-data",
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                storage_class_name=storage_class_name,
                resources=k8s.core.v1.ResourceRequirementsArgs(requests={"storage": storage_size}),
            ),
        )
    ]

    # Prepare pod template spec
    template_spec = {
        "containers": [container],
    }

    if volumes:
        template_spec["volumes"] = volumes
    if service_account_name:
        template_spec["serviceAccountName"] = service_account_name
    if node_selector:
        template_spec["nodeSelector"] = node_selector
    if tolerations:
        template_spec["tolerations"] = tolerations
    if affinity:
        template_spec["affinity"] = affinity
    if security_context:
        template_spec["securityContext"] = security_context
    if image_pull_secrets:
        template_spec["imagePullSecrets"] = image_pull_secrets

    # Create stateful set
    return k8s.apps.v1.StatefulSet(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
        spec=k8s.apps.v1.StatefulSetSpecArgs(
            replicas=replicas,
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=pod_labels or {"app": name}),
            service_name=name,
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels=pod_labels or {"app": name},
                    annotations=pod_annotations or {},
                ),
                spec=template_spec,
            ),
            volume_claim_templates=volume_claim_templates,
            update_strategy=update_strategy,
        ),
        opts=opts or ResourceOptions(provider=provider),
    )
