"""
Kubernetes ServiceAccount and RBAC resource implementations.
"""
from typing import Dict, Any, Optional, List, Union
from pulumi import ResourceOptions, Output
import pulumi_kubernetes as k8s


def create_service_account(
    name: str,
    namespace: str,
    provider: k8s.Provider,
    image_pull_secrets: Optional[List[Dict[str, str]]] = None,
    automount_token: Optional[bool] = None,
    secrets: Optional[List[Dict[str, str]]] = None,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.core.v1.ServiceAccount:
    """
    Create a Kubernetes ServiceAccount with standard configuration.

    Args:
        name: Name of the service account
        namespace: Namespace for the service account
        provider: Kubernetes provider
        image_pull_secrets: Optional list of image pull secrets
        automount_token: Optional flag to automount API token
        secrets: Optional list of secrets
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.core.v1.ServiceAccount: Created ServiceAccount resource
    """
    args = {
        "metadata": k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        )
    }

    if image_pull_secrets:
        args["image_pull_secrets"] = image_pull_secrets

    if automount_token is not None:
        args["automount_service_account_token"] = automount_token

    if secrets:
        args["secrets"] = secrets

    return k8s.core.v1.ServiceAccount(
        name,
        **args,
        opts=opts or ResourceOptions(provider=provider),
    )


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
            cluster_role_selectors=[{
                "match_labels": labels_selector
            }]
        )

    return k8s.rbac.v1.ClusterRole(
        name,
        metadata=metadata,
        rules=rules or [],
        opts=opts or ResourceOptions(provider=provider),
    )


def create_workload_service_account(
    name: str,
    namespace: str,
    provider: k8s.Provider,
    role_rules: List[Dict[str, Any]],
    cluster_role_rules: Optional[List[Dict[str, Any]]] = None,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> Dict[str, Union[k8s.core.v1.ServiceAccount, k8s.rbac.v1.Role, k8s.rbac.v1.RoleBinding, k8s.rbac.v1.ClusterRole, k8s.rbac.v1.ClusterRoleBinding]]:
    """
    Create a ServiceAccount with associated Role, RoleBinding, ClusterRole, and ClusterRoleBinding for workloads.

    Args:
        name: Base name for the resources
        namespace: Namespace for the resources
        provider: Kubernetes provider
        role_rules: List of rules for the Role
        cluster_role_rules: Optional list of rules for ClusterRole
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        Dict containing created ServiceAccount, Role, RoleBinding, ClusterRole, and ClusterRoleBinding resources
    """
    # Create ServiceAccount
    service_account = create_service_account(
        name=name,
        namespace=namespace,
        provider=provider,
        labels=labels,
        annotations=annotations,
        opts=opts,
    )

    # Create Role
    role = create_role(
        name=f"{name}-role",
        namespace=namespace,
        rules=role_rules,
        provider=provider,
        labels=labels,
        annotations=annotations,
        opts=opts or ResourceOptions(provider=provider, parent=service_account),
    )

    # Create RoleBinding
    role_binding = create_role_binding(
        name=f"{name}-rolebinding",
        namespace=namespace,
        subjects=[{
            "kind": "ServiceAccount",
            "name": name,
            "namespace": namespace,
        }],
        role_ref={
            "kind": "Role",
            "name": f"{name}-role",
            "apiGroup": "rbac.authorization.k8s.io",
        },
        provider=provider,
        labels=labels,
        annotations=annotations,
        opts=opts or ResourceOptions(provider=provider, parent=role),
    )

    resources = {
        "service_account": service_account,
        "role": role,
        "role_binding": role_binding,
    }

    # Optionally create ClusterRole and ClusterRoleBinding
    if cluster_role_rules:
        cluster_role = create_cluster_role(
            name=f"{name}-cluster-role",
            rules=cluster_role_rules,
            provider=provider,
            labels=labels,
            annotations=annotations,
            opts=opts or ResourceOptions(provider=provider, parent=service_account),
        )

        cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
            f"{name}-cluster-rolebinding",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"{name}-cluster-rolebinding",
                labels=labels or {},
                annotations=annotations or {},
            ),
            subjects=[{
                "kind": "ServiceAccount",
                "name": name,
                "namespace": namespace,
            }],
            role_ref={
                "kind": "ClusterRole",
                "name": f"{name}-cluster-role",
                "apiGroup": "rbac.authorization.k8s.io",
            },
            opts=opts or ResourceOptions(provider=provider, parent=cluster_role),
        )

        resources.update({
            "cluster_role": cluster_role,
            "cluster_role_binding": cluster_role_binding,
        })

    return resources
