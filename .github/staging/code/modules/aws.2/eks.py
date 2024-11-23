# pulumi/modules/aws/eks.py

"""
AWS EKS Management Module

Handles creation and management of EKS clusters including:
- Cluster creation and configuration
- Node group management
- Add-on deployment
- Security and networking integration
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import json
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

if TYPE_CHECKING:
    from .types import EksConfig, EksNodeGroupConfig, EksAddonConfig
    from .provider import AWSProvider

class EksManager:
    """
    Manages EKS clusters and related resources.

    This class handles:
    - Cluster provisioning
    - Node group management
    - Add-on deployment
    - IAM integration
    """

    def __init__(self, provider: 'AWSProvider'):
        """
        Initialize EKS manager.

        Args:
            provider: AWSProvider instance for resource management
        """
        self.provider = provider

    def create_cluster(
        self,
        config: 'EksConfig',
        vpc_id: str,
        subnet_ids: List[str],
        opts: Optional[ResourceOptions] = None
    ) -> aws.eks.Cluster:
        """
        Creates an EKS cluster with specified configuration.

        Args:
            config: EKS configuration
            vpc_id: VPC ID for the cluster
            subnet_ids: Subnet IDs for the cluster
            opts: Optional resource options

        Returns:
            aws.eks.Cluster: Created EKS cluster
        """
        # Create cluster role
        cluster_role = self._create_cluster_role()

        # Create KMS key for secrets encryption if enabled
        kms_key = None
        if config.enable_secrets_encryption:
            kms_key = self.provider.security.create_kms_key(
                f"eks-{config.cluster_name}-secrets",
                description=f"KMS key for EKS cluster {config.cluster_name} secrets",
                opts=opts
            )

        # Create the cluster
        cluster = aws.eks.Cluster(
            config.cluster_name,
            name=config.cluster_name,
            role_arn=cluster_role.arn,
            version=config.kubernetes_version,
            vpc_config=aws.eks.ClusterVpcConfigArgs(
                subnet_ids=subnet_ids,
                endpoint_private_access=config.endpoint_private_access,
                endpoint_public_access=config.endpoint_public_access,
            ),
            encryption_config=[aws.eks.ClusterEncryptionConfigArgs(
                provider=aws.eks.ProviderArgs(
                    key_arn=kms_key.arn
                ),
                resources=["secrets"]
            )] if config.enable_secrets_encryption else None,
            enabled_cluster_log_types=[
                "api",
                "audit",
                "authenticator",
                "controllerManager",
                "scheduler"
            ],
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Enable IRSA if configured
        if config.enable_irsa:
            self._enable_irsa(cluster, config.cluster_name, opts)

        # Create node groups
        for node_group_config in config.node_groups:
            self.create_node_group(
                cluster,
                node_group_config,
                subnet_ids,
                opts
            )

        # Deploy add-ons
        if config.addons:
            self._deploy_addons(cluster, config.addons, opts)

        return cluster

    def create_node_group(
        self,
        cluster: aws.eks.Cluster,
        config: 'EksNodeGroupConfig',
        subnet_ids: List[str],
        opts: Optional[ResourceOptions] = None
    ) -> aws.eks.NodeGroup:
        """
        Creates an EKS node group.

        Args:
            cluster: EKS cluster
            config: Node group configuration
            subnet_ids: Subnet IDs for the node group
            opts: Optional resource options

        Returns:
            aws.eks.NodeGroup: Created node group
        """
        # Create node role
        node_role = self._create_node_role()

        # Create launch template
        launch_template = self._create_launch_template(
            cluster.name,
            config,
            opts
        )

        # Create the node group
        return aws.eks.NodeGroup(
            f"{cluster.name}-{config.name}",
            cluster_name=cluster.name,
            node_group_name=config.name,
            node_role_arn=node_role.arn,
            subnet_ids=subnet_ids,
            scaling_config=aws.eks.NodeGroupScalingConfigArgs(
                desired_size=config.desired_size,
                max_size=config.max_size,
                min_size=config.min_size
            ),
            instance_types=[config.instance_type],
            capacity_type=config.capacity_type,
            ami_type=config.ami_type,
            disk_size=config.disk_size,
            labels=config.labels,
            tags=self.provider.get_tags(),
            launch_template=aws.eks.NodeGroupLaunchTemplateArgs(
                id=launch_template.id,
                version=launch_template.latest_version
            ),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True,
                    parent=cluster
                ),
                opts
            )
        )

    def _create_cluster_role(self) -> aws.iam.Role:
        """Creates IAM role for EKS cluster."""
        return self.provider.iam.create_role(
            "eks-cluster",
            assume_role_policy={
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "eks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }]
            },
            policies=[
                "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
                "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
            ]
        )

    def _create_node_role(self) -> aws.iam.Role:
        """Creates IAM role for EKS nodes."""
        return self.provider.iam.create_role(
            "eks-node",
            assume_role_policy={
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }]
            },
            policies=[
                "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
                "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
                "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
            ]
        )

    def _create_launch_template(
        self,
        cluster_name: str,
        config: 'EksNodeGroupConfig',
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.LaunchTemplate:
        """Creates launch template for node group."""
        return aws.ec2.LaunchTemplate(
            f"{cluster_name}-{config.name}",
            name_prefix=f"{cluster_name}-{config.name}",
            block_device_mappings=[aws.ec2.LaunchTemplateBlockDeviceMappingArgs(
                device_name="/dev/xvda",
                ebs=aws.ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
                    volume_size=config.disk_size,
                    volume_type="gp3",
                    encrypted=True
                )
            )],
            metadata_options=aws.ec2.LaunchTemplateMetadataOptionsArgs(
                http_endpoint="enabled",
                http_tokens="required",
                http_put_response_hop_limit=2
            ),
            monitoring=aws.ec2.LaunchTemplateMonitoringArgs(
                enabled=True
            ),
            tags=self.provider.get_tags(),
            opts=opts
        )

    def _enable_irsa(
        self,
        cluster: aws.eks.Cluster,
        cluster_name: str,
        opts: Optional[ResourceOptions] = None
    ) -> None:
        """Enables IAM Roles for Service Accounts."""
        # Create OpenID Connect Provider
        oidc_url = cluster.identities[0].oidcs[0].issuer
        oidc_provider = aws.iam.OpenIdConnectProvider(
            f"{cluster_name}-oidc",
            client_id_lists=["sts.amazonaws.com"],
            thumbprint_lists=["9e99a48a9960b14926bb7f3b02e22da2b0ab7280"],
            url=oidc_url,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    parent=cluster
                ),
                opts
            )
        )

    def _deploy_addons(
        self,
        cluster: aws.eks.Cluster,
        addons: 'EksAddonConfig',
        opts: Optional[ResourceOptions] = None
    ) -> None:
        """Deploys EKS add-ons."""
        if addons.vpc_cni:
            aws.eks.Addon(
                f"{cluster.name}-vpc-cni",
                cluster_name=cluster.name,
                addon_name="vpc-cni",
                resolve_conflicts="OVERWRITE",
                tags=self.provider.get_tags(),
                opts=ResourceOptions.merge(
                    ResourceOptions(
                        provider=self.provider.provider,
                        parent=cluster
                    ),
                    opts
                )
            )

        # Add other add-ons similarly
        # TODO: Implement remaining add-ons
