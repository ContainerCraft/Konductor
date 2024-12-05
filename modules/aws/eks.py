"""AWS EKS Management Module"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import pulumi_aws as aws
from pulumi import ResourceOptions, log
import pulumi_kubernetes as k8s
import pulumi

if TYPE_CHECKING:
    from .provider import AWSProvider


class EksManager:
    """Manages AWS EKS cluster and related resources."""

    def __init__(self, provider: "AWSProvider"):
        """Initialize EKS manager."""
        self.provider = provider

    def create_vpc(self, name: str) -> Dict[str, Any]:
        """Create VPC and related networking resources for EKS."""
        try:
            # Create VPC
            vpc = aws.ec2.Vpc(
                f"eks-vpc-{name}",
                cidr_block="10.0.0.0/16",
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-vpc-{name}",
                    "kubernetes.io/cluster/{name}": "shared",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Create Internet Gateway
            igw = aws.ec2.InternetGateway(
                f"eks-igw-{name}",
                vpc_id=vpc.id,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-igw-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Create public and private subnets across 2 AZs
            public_subnets = []
            private_subnets = []
            azs = ["us-east-1a", "us-east-1b"]  # Hardcoded for first iteration

            for i, az in enumerate(azs):
                # Public subnet
                public_subnet = aws.ec2.Subnet(
                    f"eks-public-subnet-{name}-{i}",
                    vpc_id=vpc.id,
                    cidr_block=f"10.0.{i*2}.0/24",
                    availability_zone=az,
                    map_public_ip_on_launch=True,
                    tags={
                        **self.provider.get_tags(),
                        "Name": f"eks-public-{name}-{i}",
                        "kubernetes.io/cluster/{name}": "shared",
                        "kubernetes.io/role/elb": "1",
                    },
                    opts=ResourceOptions(provider=self.provider.provider),
                )
                public_subnets.append(public_subnet)

                # Private subnet
                private_subnet = aws.ec2.Subnet(
                    f"eks-private-subnet-{name}-{i}",
                    vpc_id=vpc.id,
                    cidr_block=f"10.0.{i*2+1}.0/24",
                    availability_zone=az,
                    tags={
                        **self.provider.get_tags(),
                        "Name": f"eks-private-{name}-{i}",
                        "kubernetes.io/cluster/{name}": "shared",
                        "kubernetes.io/role/internal-elb": "1",
                    },
                    opts=ResourceOptions(provider=self.provider.provider),
                )
                private_subnets.append(private_subnet)

            # Create route table for public subnets
            public_rt = aws.ec2.RouteTable(
                f"eks-public-rt-{name}",
                vpc_id=vpc.id,
                routes=[
                    {
                        "cidr_block": "0.0.0.0/0",
                        "gateway_id": igw.id,
                    }
                ],
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-public-rt-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Associate public subnets with public route table
            for i, subnet in enumerate(public_subnets):
                aws.ec2.RouteTableAssociation(
                    f"eks-public-rta-{name}-{i}",
                    subnet_id=subnet.id,
                    route_table_id=public_rt.id,
                    opts=ResourceOptions(provider=self.provider.provider),
                )

            # Create NAT Gateway for private subnets
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

            # Create route table for private subnets
            private_rt = aws.ec2.RouteTable(
                f"eks-private-rt-{name}",
                vpc_id=vpc.id,
                routes=[
                    {
                        "cidr_block": "0.0.0.0/0",
                        "nat_gateway_id": nat_gateway.id,
                    }
                ],
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-private-rt-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider),
            )

            # Associate private subnets with private route table
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
        """Create IAM role for EKS cluster."""
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "eks.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }

        role = aws.iam.Role(
            f"eks-cluster-role-{name}",
            assume_role_policy=assume_role_policy,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(provider=self.provider.provider),
        )

        # Attach required policies
        aws.iam.RolePolicyAttachment(
            f"eks-cluster-policy-{name}",
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
            role=role.name,
            opts=ResourceOptions(provider=self.provider.provider),
        )

        return role

    def create_node_role(self, name: str) -> aws.iam.Role:
        """Create IAM role for EKS node group."""
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }

        role = aws.iam.Role(
            f"eks-node-role-{name}",
            assume_role_policy=assume_role_policy,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(provider=self.provider.provider),
        )

        # Attach required policies
        required_policies = ["AmazonEKSWorkerNodePolicy", "AmazonEKS_CNI_Policy", "AmazonEC2ContainerRegistryReadOnly"]

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
        """Create EKS cluster."""
        if tags is None:
            tags = {}

        # Merge with provider tags
        merged_tags = {**self.provider.get_tags(), **tags}

        # Create the EKS cluster
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
        """Create EKS node group."""
        if instance_types is None:
            instance_types = ["t3.medium"]

        if scaling_config is None:
            scaling_config = {"desired_size": 2, "max_size": 4, "min_size": 1}

        if tags is None:
            tags = {}

        # Merge with provider tags
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

    def deploy_test_nginx(self, k8s_provider: k8s.Provider, name: str) -> k8s.core.v1.Pod:
        """Deploy a test nginx pod to verify cluster functionality."""
        try:
            nginx_pod = k8s.core.v1.Pod(
                f"nginx-test-{name}",
                metadata={"name": f"nginx-test-{name}", "namespace": "default"},
                spec={"containers": [{"name": "nginx", "image": "nginx:latest", "ports": [{"containerPort": 80}]}]},
                opts=ResourceOptions(
                    provider=k8s_provider,
                    depends_on=[k8s_provider],
                    custom_timeouts={"create": "5m", "delete": "5m"}),
            )
            return nginx_pod

        except Exception as e:
            log.error(f"Failed to deploy test nginx pod: {str(e)}")
            return None

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
            # Create VPC infrastructure
            vpc_resources = self.create_vpc(name)

            # Use private subnets for the EKS cluster
            subnet_ids = [subnet.id for subnet in vpc_resources["private_subnets"]]

            # Create IAM roles
            cluster_role = self.create_cluster_role(name)
            node_role = self.create_node_role(name)

            # Create EKS cluster
            cluster = self.create_cluster(name=name, subnet_ids=subnet_ids, cluster_role=cluster_role, version=version)
            cluster_name = cluster.name.apply(lambda n: n)

            # Create node group
            node_group = self.create_node_group(
                name=name,
                cluster=cluster,
                node_role=node_role,
                subnet_ids=subnet_ids,
                instance_types=instance_types,
                scaling_config=scaling_config,
            )

            # Generate an external kubeconfig using cluster properties for use with kubectl
            # This is not used by the Pulumi provider, but is useful for local testing
            aws_auth_args = ["eks", "get-token", "--cluster-name", name]
            if self.provider.config.profile:
                aws_auth_args = ["--profile", self.provider.config.profile] + aws_auth_args

            external_kubeconfig = pulumi.Output.all(
                cluster.endpoint, cluster.certificate_authority.apply(lambda ca: ca.data)
            ).apply(
                lambda args: {
                    "apiVersion": "v1",
                    "clusters": [
                        {
                            "cluster": {"server": args[0], "certificate-authority-data": args[1]},
                            "name": "kubernetes",
                        }
                    ],
                    "contexts": [
                        {
                            "context": {
                                "cluster": "kubernetes",
                                "user": "aws",
                            },
                            "name": "aws",
                        }
                    ],
                    "current-context": "aws",
                    "kind": "Config",
                    "users": [
                        {
                            "name": "aws",
                            "user": {
                                "exec": {
                                    "apiVersion": "client.authentication.k8s.io/v1beta1",
                                    "command": "aws",
                                    "args": aws_auth_args,
                                }
                            },
                        }
                    ],
                }
            )

            # Get cluster auth token using Pulumi's built-in AWS provider
            try:
                cluster_token = aws.eks.get_cluster_auth(
                    name=cluster_name, opts=pulumi.InvokeOptions(
                        provider=self.provider.provider,
                        depends_on=[cluster]
                    )
                )
            except Exception as e:
                log.error(f"Failed to get cluster auth token: {str(e)}")
                raise

            # Generate kubeconfig using direct token authentication
            internal_kubeconfig = pulumi.Output.all(
                cluster.endpoint, cluster.certificate_authority.apply(lambda ca: ca.data), cluster_token.token
            ).apply(
                lambda args: {
                    "apiVersion": "v1",
                    "clusters": [
                        {"cluster": {"server": args[0], "certificate-authority-data": args[1]}, "name": "kubernetes"}
                    ],
                    "contexts": [{"context": {"cluster": "kubernetes", "user": "aws"}, "name": "aws"}],
                    "current-context": "aws",
                    "kind": "Config",
                    "users": [{"name": "aws", "user": {"token": args[2]}}],
                }
            )

            # Create k8s provider with the internal kubeconfig
            k8s_provider = k8s.Provider(
                f"k8s-provider-{name}",
                kubeconfig=internal_kubeconfig.apply(lambda c: pulumi.Output.json_dumps(c)),
                opts=ResourceOptions(depends_on=[cluster]),
            )

            # Export both kubeconfigs with descriptive names
            pulumi.export("eks_kubeconfig_external", pulumi.Output.secret(external_kubeconfig))

            # Deploy test nginx pod
            self.deploy_test_nginx(k8s_provider, name)

            return {
                "vpc": vpc_resources["vpc"],
                "public_subnets": vpc_resources["public_subnets"],
                "private_subnets": vpc_resources["private_subnets"],
                "cluster": cluster,
                "node_group": node_group,
                "cluster_role": cluster_role,
                "node_role": node_role,
                "kubeconfig": external_kubeconfig,
                "internal_kubeconfig": internal_kubeconfig,
                "k8s_provider": k8s_provider,
            }

        except Exception as e:
            log.error(f"Failed to deploy EKS cluster: {str(e)}")
            raise
