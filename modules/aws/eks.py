# ./modules/aws/eks.py
"""AWS EKS Management Module

This module provides an opinionated way to manage and deploy an EKS cluster and related
infrastructure using Pulumi.

Features:
- Creates a VPC, subnets, route tables, and NAT gateway resources suitable for EKS.
- Sets up IAM roles for the EKS cluster and node groups.
- Provisions the EKS cluster and node groups.
- Generates a kubeconfig that uses IAM role-based temporary credentials retrieved
    programmatically via AWS SDK calls, removing the need for external CLI tools like
    `aws-iam-authenticator`.
- Creates a Pulumi Kubernetes provider that uses the generated kubeconfig.
- Optionally deploys a test Nginx Pod to verify the cluster functionality.

This design ensures no shelling out to external CLI tools;
all authentication is done through IAM roles and
AWS APIs directly via Pulumi's `aws.eks.get_cluster_auth`.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import pulumi_aws as aws
from pulumi import ResourceOptions, log
import pulumi_kubernetes as k8s
import pulumi
import json

if TYPE_CHECKING:
    from .provider import AWSProvider


class EksManager:
    """Manages AWS EKS cluster and related resources."""

    def __init__(self, provider: "AWSProvider"):
        """
        Initialize EKS manager with a given AWS provider.

        :param provider: AWSProvider instance that includes configuration,
                            credentials, or assume-role details.
        """
        self.provider = provider

    def create_vpc(self, name: str) -> Dict[str, Any]:
        """
        Create a new VPC, subnets (public and private), and associated routing
        infrastructure suitable for hosting an EKS cluster.

        :param name: A unique name suffix for all created resources.
        :return: A dictionary containing references to created VPC and subnets:
                 {
                     "vpc": <aws.ec2.Vpc>,
                     "public_subnets": [aws.ec2.Subnet, ...],
                     "private_subnets": [aws.ec2.Subnet, ...]
                 }
        """
        try:
            # Create the VPC
            vpc = aws.ec2.Vpc(
                f"eks-vpc-{name}",
                cidr_block="10.0.0.0/16",
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-vpc-{name}",
                    f"kubernetes.io/cluster/{name}": "shared",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Create Internet Gateway for public connectivity
            igw = aws.ec2.InternetGateway(
                f"eks-igw-{name}",
                vpc_id=vpc.id,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-igw-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Hardcoded AZs for simplicity. Adjust as needed.
            azs = ["us-east-1a", "us-east-1b"]

            public_subnets = []
            private_subnets = []

            for i, az in enumerate(azs):
                # Create a public subnet in each AZ
                public_subnet = aws.ec2.Subnet(
                    f"eks-public-subnet-{name}-{i}",
                    vpc_id=vpc.id,
                    cidr_block=f"10.0.{i*2}.0/24",
                    availability_zone=az,
                    map_public_ip_on_launch=True,
                    tags={
                        **self.provider.get_tags(),
                        "Name": f"eks-public-{name}-{i}",
                        f"kubernetes.io/cluster/{name}": "shared",
                        "kubernetes.io/role/elb": "1",
                    },
                    opts=ResourceOptions(provider=self.provider.provider),
                )
                public_subnets.append(public_subnet)

                # Create a private subnet in each AZ
                private_subnet = aws.ec2.Subnet(
                    f"eks-private-subnet-{name}-{i}",
                    vpc_id=vpc.id,
                    cidr_block=f"10.0.{i*2+1}.0/24",
                    availability_zone=az,
                    tags={
                        **self.provider.get_tags(),
                        "Name": f"eks-private-{name}-{i}",
                        f"kubernetes.io/cluster/{name}": "shared",
                        "kubernetes.io/role/internal-elb": "1",
                    },
                    opts=ResourceOptions(provider=self.provider.provider),
                )
                private_subnets.append(private_subnet)

            # Route table for public subnets
            public_rt = aws.ec2.RouteTable(
                f"eks-public-rt-{name}",
                vpc_id=vpc.id,
                routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": igw.id}],
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-public-rt-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Associate public subnets with the public route table
            for i, subnet in enumerate(public_subnets):
                aws.ec2.RouteTableAssociation(
                    f"eks-public-rta-{name}-{i}",
                    subnet_id=subnet.id,
                    route_table_id=public_rt.id,
                    opts=ResourceOptions(provider=self.provider.provider),
                )

            # Create EIP and NAT Gateway for private subnets outgoing traffic
            eip = aws.ec2.Eip(
                f"eks-eip-{name}",
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-eip-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            nat_gateway = aws.ec2.NatGateway(
                f"eks-nat-{name}",
                allocation_id=eip.id,
                subnet_id=public_subnets[0].id,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-nat-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Route table for private subnets
            private_rt = aws.ec2.RouteTable(
                f"eks-private-rt-{name}",
                vpc_id=vpc.id,
                routes=[{"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway.id}],
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-private-rt-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Associate private subnets with the private route table
            for i, subnet in enumerate(private_subnets):
                aws.ec2.RouteTableAssociation(
                    f"eks-private-rta-{name}-{i}",
                    subnet_id=subnet.id,
                    route_table_id=private_rt.id,
                    opts=ResourceOptions(provider=self.provider.provider),
                )

            return {
                "vpc": vpc,
                "public_subnets": public_subnets,
                "private_subnets": private_subnets,
            }

        except Exception as e:
            log.error(f"Failed to create VPC infrastructure: {str(e)}")
            raise

    def create_cluster_role(self, name: str) -> aws.iam.Role:
        """
        Create the IAM role for the EKS cluster control plane.

        :param name: Name suffix for role identification.
        :return: The created IAM Role for the EKS cluster.
        """
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "eks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ],
        }

        role = aws.iam.Role(
            f"eks-cluster-role-{name}",
            assume_role_policy=assume_role_policy,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(provider=self.provider.provider),
        )

        # Attach the AmazonEKSClusterPolicy for EKS cluster management
        aws.iam.RolePolicyAttachment(
            f"eks-cluster-policy-{name}",
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
            role=role.name,
            opts=ResourceOptions(provider=self.provider.provider),
        )

        return role

    def create_node_role(self, name: str) -> aws.iam.Role:
        """
        Create the IAM role for EKS nodes (worker nodes).

        :param name: Name suffix for role identification.
        :return: The created IAM Role for EKS worker nodes.
        """
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ],
        }

        role = aws.iam.Role(
            f"eks-node-role-{name}",
            assume_role_policy=assume_role_policy,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(provider=self.provider.provider),
        )

        # Attach required policies for EKS worker nodes
        required_policies = [
            "AmazonEKSWorkerNodePolicy",
            "AmazonEKS_CNI_Policy",
            "AmazonEC2ContainerRegistryReadOnly"
        ]

        for policy in required_policies:
            aws.iam.RolePolicyAttachment(
                f"eks-node-policy-{policy}-{name}",
                policy_arn=f"arn:aws:iam::aws:policy/{policy}",
                role=role.name,
                opts=ResourceOptions(provider=self.provider.provider),
            )

        return role

    def create_cluster(
        self,
        name: str,
        subnet_ids: List[str],
        cluster_role: aws.iam.Role,
        version: Optional[str] = "1.27",
        tags: Optional[Dict[str, str]] = None,
    ) -> aws.eks.Cluster:
        """
        Create the EKS cluster control plane.

        :param name: Name of the cluster.
        :param subnet_ids: Subnets for placing the EKS endpoints.
        :param cluster_role: IAM role for the cluster control plane.
        :param version: Kubernetes version of the EKS cluster.
        :param tags: Additional tags for the cluster.
        :return: The created EKS cluster resource.
        """
        if tags is None:
            tags = {}

        merged_tags = {**self.provider.get_tags(), **tags}

        cluster = aws.eks.Cluster(
            f"eks-{name}",
            name=name,
            role_arn=cluster_role.arn,
            version=version,
            vpc_config=aws.eks.ClusterVpcConfigArgs(
                subnet_ids=subnet_ids,
                endpoint_private_access=True,
                endpoint_public_access=True,
            ),
            tags=merged_tags,
            opts=ResourceOptions(provider=self.provider.provider, protect=True),
        )

        return cluster

    def create_node_group(
        self,
        name: str,
        cluster: aws.eks.Cluster,
        node_role: aws.iam.Role,
        subnet_ids: List[str],
        instance_types: Optional[List[str]] = None,
        scaling_config: Optional[Dict[str, int]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> aws.eks.NodeGroup:
        """
        Create an EKS node group (worker nodes) attached to the EKS cluster.

        :param name: Name for identifying the node group.
        :param cluster: The EKS cluster resource.
        :param node_role: IAM role for the nodes.
        :param subnet_ids: Subnets where the worker nodes will run.
        :param instance_types: Optional EC2 instance types for worker nodes.
        :param scaling_config: Optional scaling config with desired, min, and max sizes.
        :param tags: Additional tags for the node group.
        :return: The created EKS NodeGroup resource.
        """
        if instance_types is None:
            instance_types = ["t3.medium"]

        if scaling_config is None:
            scaling_config = {"desired_size": 2, "max_size": 4, "min_size": 1}

        if tags is None:
            tags = {}

        merged_tags = {**self.provider.get_tags(), **tags}

        node_group = aws.eks.NodeGroup(
            f"eks-nodegroup-{name}",
            cluster_name=cluster.name,
            node_role_arn=node_role.arn,
            subnet_ids=subnet_ids,
            instance_types=instance_types,
            scaling_config=scaling_config,
            tags=merged_tags,
            opts=ResourceOptions(provider=self.provider.provider, depends_on=[cluster]),
        )

        return node_group

    def deploy_cluster(
        self,
        name: str,
        version: Optional[str] = None,
        instance_types: Optional[List[str]] = None,
        scaling_config: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Deploy a complete EKS cluster with VPC, node group, and test nginx pod.
        Returns cluster information and resources.
        """
        try:
            # Step 1: Create VPC and networking
            vpc_resources = self.create_vpc(name)

            # Use private subnets for the EKS cluster control plane
            subnet_ids = [subnet.id for subnet in vpc_resources["private_subnets"]]

            # Step 2: Create IAM roles for cluster and node group
            cluster_role = self.create_cluster_role(name)
            node_role = self.create_node_role(name)

            # Step 3: Create EKS cluster
            cluster = self.create_cluster(
                name=name,
                subnet_ids=subnet_ids,
                cluster_role=cluster_role,
                version=version
            )

            # Step 4: Create a node group
            node_group = self.create_node_group(
                name=name,
                cluster=cluster,
                node_role=node_role,
                subnet_ids=subnet_ids,
                instance_types=instance_types,
                scaling_config=scaling_config,
            )

            # Step 5: Generate IAM-based kubeconfig
            log.debug(f"AWS profile: {self.provider.config.profile}")
            log.debug(f"Generating IAM-based kubeconfig for {name}")
            internal_kubeconfig = pulumi.Output.all(
                name=cluster.name,
                endpoint=cluster.endpoint,
                cert_auth=cluster.certificate_authority,
                profile=self.provider.config.profile
            ).apply(
                lambda args: {
                    "apiVersion": "v1",
                    "clusters": [{
                        "cluster": {
                            "server": args["endpoint"],
                            "certificate-authority-data": args["cert_auth"]["data"]
                        },
                        "name": "kubernetes"
                    }],
                    "contexts": [{
                        "context": {
                            "cluster": "kubernetes",
                            "user": "aws"
                        },
                        "name": "aws"
                    }],
                    "current-context": "aws",
                    "kind": "Config",
                    "preferences": {},
                    "users": [{
                        "name": "aws",
                        "user": {
                            "exec": {
                                "apiVersion": "client.authentication.k8s.io/v1beta1",
                                "command": "aws-iam-authenticator",
                                "args": [
                                    "token",
                                    "-i",
                                    args["name"]
                                ],
                                "env": [
                                    {
                                        "name": "AWS_PROFILE",
                                        "value": args["profile"] or "default"
                                    }
                                ]
                            }
                        }
                    }]
                }
            )

            # Step 6: Create k8s provider with IAM-based kubeconfig
            log.debug(f"Creating k8s provider for {name}")
            k8s_provider = k8s.Provider(
                f"k8s-provider-{name}",
                kubeconfig=internal_kubeconfig.apply(json.dumps),
                opts=ResourceOptions(
                    depends_on=[cluster, node_group]
                )
            )

            # Step 7: Deploy test nginx pod with the new provider
            self.deploy_test_nginx(k8s_provider, name)

            # Return references to all major resources and configurations
            return {
                "vpc": vpc_resources["vpc"],
                "public_subnets": vpc_resources["public_subnets"],
                "private_subnets": vpc_resources["private_subnets"],
                "cluster": cluster,
                "node_group": node_group,
                "cluster_role": cluster_role,
                "node_role": node_role,
                "kubeconfig": internal_kubeconfig,
                "k8s_provider": k8s_provider,
            }

        except Exception as e:
            log.error(f"Failed to deploy EKS cluster: {str(e)}")
            raise

    def deploy_test_nginx(
        self,
        k8s_provider: k8s.Provider,
        name: str
    ) -> Optional[k8s.core.v1.Pod]:
        """
        Deploy a simple test nginx Pod to verify cluster and provider functionality.

        :param k8s_provider: The Kubernetes provider resource configured with the cluster's kubeconfig.
        :param name: Name suffix for the test pod resource.
        :return: The created Pod resource, or None if deployment fails.
        """
        try:
            log.debug(f"Deploying test Nginx pod for cluster {name}")
            nginx_pod = k8s.core.v1.Pod(
                f"nginx-test-{name}",
                metadata={"name": f"nginx-test-{name}", "namespace": "default"},
                spec={
                    "containers": [{
                        "name": "nginx",
                        "image": "nginx:latest",
                        "ports": [{"containerPort": 80}]
                    }]
                },
                opts=ResourceOptions(
                    provider=k8s_provider,
                    depends_on=[k8s_provider],
                    custom_timeouts={"create": "1m", "delete": "1m"}
                ),
            )
            return nginx_pod
        except Exception as e:
            log.error(f"Failed to deploy test Nginx pod: {str(e)}")
            return None
