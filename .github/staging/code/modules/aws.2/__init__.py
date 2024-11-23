# ./pulumi/modules/aws/__init__.py
"""
AWS Cloud Infrastructure Module

Provides AWS infrastructure management capabilities including organizations,
networking, and resource provisioning with built-in compliance controls.
"""
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
import pulumi

from .types import AWSConfig
from .provider import AWSProvider
from .organization import AWSOrganization
from .resources import ResourceManager
from .networking import NetworkManager
from .iam import IAMManager
from .eks import EksManager
from .security import SecurityManager
from .exceptions import ResourceCreationError, ConfigurationError

if TYPE_CHECKING:
    from pulumi import Resource

__all__ = [
    'AWSProvider',
    'AWSOrganization',
    'ResourceManager',
    'NetworkManager',
    'IAMManager',
    'EksManager',
    'SecurityManager',
    'AWSConfig',
    'create_aws_infrastructure',
    'ResourceCreationError',
    'ConfigurationError'
]

def create_aws_infrastructure(
    config: AWSConfig,
    dependencies: Optional[List[Resource]] = None
) -> Tuple[str, Resource, Dict[str, Any]]:
    """
    Creates AWS infrastructure based on the provided configuration.

    This is the main entry point for AWS infrastructure creation. It orchestrates
    the deployment of all AWS resources including organizations, networking,
    security controls, and workload resources.

    Args:
        config: AWS configuration settings including organization, networking,
                security, and workload configurations
        dependencies: Optional list of resources this deployment depends on

    Returns:
        Tuple containing:
            - Version string
            - Main infrastructure resource (typically the organization)
            - Dictionary of outputs including resource IDs and ARNs

    Raises:
        ValueError: If configuration is invalid
        ResourceCreationError: If resource creation fails
    """
    try:
        # Initialize provider with configuration
        provider = AWSProvider(config)

        # Create managers in dependency order
        security = SecurityManager(provider)
        networking = NetworkManager(provider)
        organization = AWSOrganization(provider)
        resources = ResourceManager(provider)
        iam = IAMManager(provider)
        eks = EksManager(provider)

        # Deploy infrastructure
        return provider.deploy(
            dependencies,
            managers={
                "security": security,
                "networking": networking,
                "organization": organization,
                "resources": resources,
                "iam": iam,
                "eks": eks
            }
        )

    except Exception as e:
        pulumi.log.error(f"Failed to create AWS infrastructure: {str(e)}")
        raise
