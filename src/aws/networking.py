# ./modules/aws/networking.py
"""AWS Networking Management Module"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

if TYPE_CHECKING:
    from .types import NetworkConfig
    from .provider import AWSProvider

class NetworkManager:
    """Manages AWS networking resources and operations."""

    def __init__(self, provider: 'AWSProvider'):
        """Initialize Network manager."""
        self.provider = provider

    def create_vpc(
        self,
        name: str,
        cidr_block: str,
        enable_dns_hostnames: bool = True,
        enable_dns_support: bool = True,
        instance_tenancy: str = "default",
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.Vpc:
        """Creates a VPC with specified configuration."""
        if opts is None:
            opts = ResourceOptions()

        vpc = aws.ec2.Vpc(
            f"vpc-{name}",
            cidr_block=cidr_block,
            enable_dns_hostnames=enable_dns_hostnames,
            enable_dns_support=enable_dns_support,
            instance_tenancy=instance_tenancy,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        return vpc

    def deploy_network_infrastructure(self) -> Dict[str, Any]:
        """Deploys networking infrastructure and returns outputs."""
        try:
            # Create VPC
            vpc = self.create_vpc(
                "main",
                self.provider.config.network.vpc_cidr
            )

            return {
                "vpc_id": vpc.id,
                "subnet_ids": []  # Add subnet creation later
            }

        except Exception as e:
            log.error(f"Failed to deploy network infrastructure: {str(e)}")
            raise
