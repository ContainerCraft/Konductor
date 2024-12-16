# ./modules/kubernetes/resources/rbac/role.py
"""
Kubernetes RBAC role resource implementations.
"""
"""
Kubernetes RBAC Role resource implementations.
"""
from typing import Dict, Any, Optional, List, Union
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s


def create_role(
    name: str,
    namespace: str,
    rules: List[Dict[str, Any]],
    provider: k8s.Provider,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.rbac.v1.Role:
    """
    Create a Kubernetes Role with standard configuration.

    Args:
        name: Name of the role
        namespace: Namespace for the role
        rules: List of role rules
        provider: Kubernetes provider
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.rbac.v1.Role: Created Role resource
    """
    return k8s.rbac.v1.Role(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
        rules=rules,
        opts=opts or ResourceOptions(provider=provider),
    )


def create_cluster_role(
    name: str,
    rules: List[Dict[str, Any]],
    provider: k8s.Provider,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.rbac.v1.ClusterRole:
    """
    Create a Kubernetes ClusterRole with standard configuration.

    Args:
        name: Name of the cluster role
        rules: List of role rules
        provider: Kubernetes provider
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.rbac.v1.ClusterRole: Created ClusterRole resource
    """
    return k8s.rbac.v1.ClusterRole(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            labels=labels or {},
            annotations=annotations or {},
        ),
        rules=rules,
        opts=opts or ResourceOptions(provider=provider),
    )


def create_role_binding(
    name: str,
    namespace: str,
    subjects: List[Dict[str, Any]],
    role_ref: Dict[str, str],
    provider: k8s.Provider,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.rbac.v1.RoleBinding:
    """
    Create a Kubernetes RoleBinding with standard configuration.

    Args:
        name: Name of the role binding
        namespace: Namespace for the role binding
        subjects: List of subjects to bind
        role_ref: Reference to the role being bound
        provider: Kubernetes provider
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.rbac.v1.RoleBinding: Created RoleBinding resource
    """
    return k8s.rbac.v1.RoleBinding(
        name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
        subjects=subjects,
        role_ref=role_ref,
        opts=opts or ResourceOptions(provider=provider),
    )


def create_aggregated_cluster_role(
    name: str,
    labels_selector: Dict[str, str],
    provider: k8s.Provider,
    rules: Optional[List[Dict[str, Any]]] = None,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.rbac.v1.ClusterRole:
    """
    Create a Kubernetes Aggregated ClusterRole with standard configuration.

    Args:
        name: Name of the aggregated cluster role
        labels_selector: Labels to select roles to aggregate
        provider: Kubernetes provider
        rules: Optional additional rules
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.rbac.v1.ClusterRole: Created aggregated ClusterRole resource
    """
    metadata = k8s.meta.v1.ObjectMetaArgs(
        name=name,
        labels=labels or {},
        annotations=annotations or {},
    )

    if labels_selector:
        metadata.aggregation_rule = k8s.rbac.v1.AggregationRuleArgs(
            cluster_role_selectors=[{"match_labels": labels_selector}]
        )

    return k8s.rbac.v1.ClusterRole(
        name,
        metadata=metadata,
        rules=rules or [],
        opts=opts or ResourceOptions(provider=provider),
    )
