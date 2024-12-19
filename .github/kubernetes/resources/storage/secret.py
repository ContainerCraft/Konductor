# ./modules/kubernetes/resources/storage/secret.py
"""
Kubernetes Secret resource implementations.
"""
from typing import Dict, Any, Optional, Union
from base64 import b64encode
from pulumi import ResourceOptions, Output
import pulumi_kubernetes as k8s


def encode_secret_data(data: Dict[str, str]) -> Dict[str, str]:
    """
    Base64 encode secret data values.

    Args:
        data: Dictionary of secret data

    Returns:
        Dict[str, str]: Dictionary with base64 encoded values
    """
    return {k: b64encode(v.encode("utf-8")).decode("utf-8") for k, v in data.items()}


def create_secret(
    name: str,
    namespace: str,
    provider: k8s.Provider,
    string_data: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, str]] = None,
    secret_type: str = "Opaque",
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.core.v1.Secret:
    """
    Create a Kubernetes Secret with standard configuration.

    Args:
        name: Name of the secret
        namespace: Namespace for the secret
        provider: Kubernetes provider
        string_data: Optional unencoded secret data
        data: Optional pre-encoded secret data
        secret_type: Type of secret (default: Opaque)
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.core.v1.Secret: Created Secret resource
    """
    args = {
        "metadata": k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
        "type": secret_type,
    }

    if string_data:
        args["string_data"] = string_data
    if data:
        args["data"] = data

    secret =k8s.core.v1.Secret(
        name,
        **args,
        opts=opts or ResourceOptions(provider=provider),
    )

    return secret


def create_tls_secret(
    name: str,
    namespace: str,
    provider: k8s.Provider,
    tls_crt: str,
    tls_key: str,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    opts: Optional[ResourceOptions] = None,
) -> k8s.core.v1.Secret:
    """
    Create a Kubernetes TLS secret.

    Args:
        name: Name of the secret
        namespace: Namespace for the secret
        provider: Kubernetes provider
        tls_crt: TLS certificate data
        tls_key: TLS private key data
        labels: Optional labels to apply
        annotations: Optional annotations to apply
        opts: Optional resource options

    Returns:
        k8s.core.v1.Secret: Created Secret resource
    """
    return create_secret(
        name=name,
        namespace=namespace,
        provider=provider,
        string_data={
            "tls.crt": tls_crt,
            "tls.key": tls_key,
        },
        secret_type="kubernetes.io/tls",
        labels=labels,
        annotations=annotations,
        opts=opts,
    )
