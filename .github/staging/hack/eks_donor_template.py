"""
Amazon EKS Cluster Deployment Template

This script deploys a production-ready Amazon EKS cluster using Pulumi and Python.
It adheres to the project's standards, including strict type checking, type hints,
and Pydantic models for configuration validation.

The script includes the following components:
- Configuration management using Pydantic models
- VPC and networking setup
- IAM roles and policies
- EKS Cluster and Node Group creation
- Kubeconfig generation
- Observability integrations (Fluent Bit)
"""

import json
from typing import List, Optional, Dict

import pulumi
from pulumi import ResourceOptions, Output, Config, log
import pulumi_aws as aws
import pulumi_kubernetes as k8s
from pydantic import BaseModel, ValidationError

# Get the current Pulumi stack name
stack_name: str = pulumi.get_stack()

# Configuration Models
class NodeGroupConfig(BaseModel):
    """Node group configuration structure.

    Attributes:
        name: The name of the node group.
        instance_type: The EC2 instance type.
        desired_capacity: The desired number of nodes.
        min_size: The minimum number of nodes.
        max_size: The maximum number of nodes.
        ssh_key_name: The name of the SSH key pair.
        tags: Optional tags for the node group resources.
    """

    name: str
    instance_type: str = "t3.medium"
    desired_capacity: int = 2
    min_size: int = 1
    max_size: int = 3
    ssh_key_name: str
    tags: Optional[Dict[str, str]] = None


class EksClusterConfig(BaseModel):
    """EKS cluster configuration structure.

    Attributes:
        name: The name of the EKS cluster.
        version: The Kubernetes version.
        region: The AWS region.
        node_groups: A list of node group configurations.
        tags: Optional tags for the cluster resources.
        ssh_key_name: The name of the SSH key pair.
        vpc_cidr: CIDR block for the VPC.
        allowed_ssh_cidr: Allowed CIDR block for SSH access.
    """

    name: str
    version: str = "1.26"
    region: str
    node_groups: List[NodeGroupConfig]
    tags: Optional[Dict[str, str]] = None
    ssh_key_name: str
    vpc_cidr: str = "10.0.0.0/16"
    allowed_ssh_cidr: str = "0.0.0.0/0"


def load_config() -> EksClusterConfig:
    """Load and validate configuration using Pydantic models.

    Returns:
        An instance of EksClusterConfig with validated configuration.
    """
    config = Config()

    try:
        eks_config = EksClusterConfig(
            name=config.require("cluster_name"),
            region=config.require("aws:region"),
            ssh_key_name=config.require("ssh_key_name"),
            node_groups=[
                NodeGroupConfig(
                    name="default-node-group",
                    instance_type=config.get("node_instance_type") or "t3.medium",
                    desired_capacity=int(config.get("desired_capacity") or 2),
                    min_size=int(config.get("min_size") or 1),
                    max_size=int(config.get("max_size") or 3),
                    ssh_key_name=config.require("ssh_key_name"),
                    tags={"environment": stack_name},
                )
            ],
            tags={"environment": stack_name},
            allowed_ssh_cidr=config.get("allowed_ssh_cidr") or "0.0.0.0/0",
        )
        return eks_config
    except ValidationError as e:
        log.error(f"Configuration validation failed: {e}")
        raise


# Load configuration
eks_config = load_config()

# Set the AWS provider
aws_provider = aws.Provider(
    "aws_provider",
    region=eks_config.region,
)

# VPC setup
def create_vpc() -> aws.ec2.Vpc:
    """Create VPC for the EKS cluster.

    Returns:
        The created VPC resource.
    """
    try:
        vpc = aws.ec2.Vpc(
            "eks-vpc",
            cidr_block=eks_config.vpc_cidr,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={"Name": "eks-vpc", **(eks_config.tags or {})},
            opts=ResourceOptions(provider=aws_provider),
        )
        return vpc
    except Exception as e:
        log.error(f"VPC creation failed: {e}")
        raise


vpc = create_vpc()

# Subnets
def create_subnets(vpc_id: Output[str]) -> List[aws.ec2.Subnet]:
    """Create public and private subnets in different availability zones.

    Args:
        vpc_id: The ID of the VPC.

    Returns:
        A list of created Subnet resources.
    """
    try:
        availability_zones = aws.get_availability_zones().names[:2]
        public_subnets = []
        private_subnets = []
        for i, az in enumerate(availability_zones):
            public_subnet = aws.ec2.Subnet(
                f"public-subnet-{i}",
                vpc_id=vpc_id,
                cidr_block=f"10.0.{i}.0/24",
                availability_zone=az,
                map_public_ip_on_launch=True,
                tags={"Name": f"public-subnet-{i}", **(eks_config.tags or {})},
                opts=ResourceOptions(provider=aws_provider),
            )
            private_subnet = aws.ec2.Subnet(
                f"private-subnet-{i}",
                vpc_id=vpc_id,
                cidr_block=f"10.0.{i+10}.0/24",
                availability_zone=az,
                map_public_ip_on_launch=False,
                tags={"Name": f"private-subnet-{i}", **(eks_config.tags or {})},
                opts=ResourceOptions(provider=aws_provider),
            )
            public_subnets.append(public_subnet)
            private_subnets.append(private_subnet)
        return public_subnets + private_subnets
    except Exception as e:
        log.error(f"Subnet creation failed: {e}")
        raise


subnets = create_subnets(vpc.id)

# Internet Gateway
def create_internet_gateway(vpc_id: Output[str]) -> aws.ec2.InternetGateway:
    """Create an Internet Gateway for the VPC.

    Args:
        vpc_id: The ID of the VPC.

    Returns:
        The created Internet Gateway resource.
    """
    try:
        igw = aws.ec2.InternetGateway(
            "igw",
            vpc_id=vpc_id,
            tags={"Name": "igw", **(eks_config.tags or {})},
            opts=ResourceOptions(provider=aws_provider),
        )
        return igw
    except Exception as e:
        log.error(f"Internet Gateway creation failed: {e}")
        raise


igw = create_internet_gateway(vpc.id)

# Route Tables
def create_route_tables(vpc_id: Output[str], igw_id: Output[str], subnets: List[aws.ec2.Subnet]) -> None:
    """Create route tables and associate them with subnets.

    Args:
        vpc_id: The ID of the VPC.
        igw_id: The ID of the Internet Gateway.
        subnets: The list of subnets.
    """
    try:
        public_route_table = aws.ec2.RouteTable(
            "public-route-table",
            vpc_id=vpc_id,
            routes=[
                aws.ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    gateway_id=igw_id,
                )
            ],
            tags={"Name": "public-route-table", **(eks_config.tags or {})},
            opts=ResourceOptions(provider=aws_provider),
        )

        for subnet in subnets:
            if subnet.map_public_ip_on_launch:
                aws.ec2.RouteTableAssociation(
                    f"public-rta-{subnet._name}",
                    subnet_id=subnet.id,
                    route_table_id=public_route_table.id,
                    opts=ResourceOptions(provider=aws_provider),
                )
    except Exception as e:
        log.error(f"Route table creation failed: {e}")
        raise


create_route_tables(vpc.id, igw.id, subnets)

# Security Groups
def create_security_groups(vpc_id: Output[str]) -> aws.ec2.SecurityGroup:
    """Create security groups for the EKS cluster.

    Args:
        vpc_id: The ID of the VPC.

    Returns:
        The created Security Group resource.
    """
    try:
        eks_security_group = aws.ec2.SecurityGroup(
            "eks-security-group",
            vpc_id=vpc_id,
            description="EKS cluster security group",
            tags={"Name": "eks-security-group", **(eks_config.tags or {})},
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    description="Allow all traffic within the security group",
                    self_=True,
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    description="Allow inbound SSH",
                    cidr_blocks=[eks_config.allowed_ssh_cidr],
                    from_port=22,
                    to_port=22,
                    protocol="tcp",
                ),
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    description="Allow all outbound traffic",
                    cidr_blocks=["0.0.0.0/0"],
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                )
            ],
            opts=ResourceOptions(provider=aws_provider),
        )
        return eks_security_group
    except Exception as e:
        log.error(f"Security Group creation failed: {e}")
        raise


eks_security_group = create_security_groups(vpc.id)

# IAM Roles and Policies
def create_iam_role(role_name: str, assume_role_policy: str, managed_policy_arns: List[str]) -> aws.iam.Role:
    """Create an IAM role with specified policies.

    Args:
        role_name: The name of the IAM role.
        assume_role_policy: The assume role policy JSON.
        managed_policy_arns: A list of managed policy ARNs.

    Returns:
        The created IAM role.
    """
    try:
        role = aws.iam.Role(
            role_name,
            assume_role_policy=assume_role_policy,
            tags=eks_config.tags,
            opts=ResourceOptions(provider=aws_provider),
        )
        for idx, policy_arn in enumerate(managed_policy_arns):
            aws.iam.RolePolicyAttachment(
                f"{role_name}-policy-{idx}",
                role=role.name,
                policy_arn=policy_arn,
                opts=ResourceOptions(provider=aws_provider),
            )
        return role
    except Exception as e:
        log.error(f"IAM Role creation failed: {e}")
        raise


eks_role = create_iam_role(
    "eks-cluster-role",
    assume_role_policy='''{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": { "Service": "eks.amazonaws.com" },
                "Effect": "Allow"
            }
        ]
    }''',
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
    ]
)

node_group_role = create_iam_role(
    "eks-nodegroup-role",
    assume_role_policy='''{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": { "Service": "ec2.amazonaws.com" },
                "Effect": "Allow"
            }
        ]
    }''',
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
        "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    ]
)

# EKS Cluster
def create_eks_cluster() -> aws.eks.Cluster:
    """Create the EKS cluster.

    Returns:
        The created EKS cluster.
    """
    try:
        cluster = aws.eks.Cluster(
            "eks-cluster",
            role_arn=eks_role.arn,
            version=eks_config.version,
            vpc_config=aws.eks.ClusterVpcConfigArgs(
                subnet_ids=[subnet.id for subnet in subnets if not subnet.map_public_ip_on_launch],
                security_group_ids=[eks_security_group.id],
            ),
            tags={"Name": "eks-cluster", **(eks_config.tags or {})},
            enabled_cluster_log_types=["api", "audit", "authenticator", "controllerManager", "scheduler"],
            opts=ResourceOptions(provider=aws_provider),
        )
        return cluster
    except Exception as e:
        log.error(f"EKS Cluster creation failed: {e}")
        raise


eks_cluster = create_eks_cluster()

# Node Group
def create_node_group(cluster: aws.eks.Cluster) -> aws.eks.NodeGroup:
    """Create a Node Group for the EKS cluster.

    Args:
        cluster: The EKS cluster.

    Returns:
        The created Node Group.
    """
    try:
        node_group_config = eks_config.node_groups[0]
        node_group = aws.eks.NodeGroup(
            "eks-node-group",
            cluster_name=cluster.name,
            node_group_name=node_group_config.name,
            node_role_arn=node_group_role.arn,
            subnet_ids=[subnet.id for subnet in subnets if not subnet.map_public_ip_on_launch],
            scaling_config=aws.eks.NodeGroupScalingConfigArgs(
                desired_size=node_group_config.desired_capacity,
                min_size=node_group_config.min_size,
                max_size=node_group_config.max_size,
            ),
            instance_types=[node_group_config.instance_type],
            remote_access=aws.eks.NodeGroupRemoteAccessArgs(
                ec2_ssh_key=node_group_config.ssh_key_name,
                source_security_group_ids=[eks_security_group.id],
            ),
            tags={"Name": node_group_config.name, **(node_group_config.tags or {})},
            opts=ResourceOptions(provider=aws_provider),
        )
        return node_group
    except Exception as e:
        log.error(f"Node Group creation failed: {e}")
        raise


node_group = create_node_group(eks_cluster)

# Kubeconfig Generation
def generate_kubeconfig(cluster: aws.eks.Cluster) -> Output[str]:
    """Generate Kubeconfig for accessing the EKS cluster.

    Args:
        cluster: The EKS cluster.

    Returns:
        The Kubeconfig content as a string.
    """
    try:
        def kubeconfig_args(cluster_name, cluster_endpoint, cluster_cert) -> str:
            kubeconfig = {
                "apiVersion": "v1",
                "clusters": [{
                    "cluster": {
                        "server": cluster_endpoint,
                        "certificate-authority-data": cluster_cert,
                    },
                    "name": "kubernetes",
                }],
                "contexts": [{
                    "context": {
                        "cluster": "kubernetes",
                        "user": "aws",
                    },
                    "name": "aws",
                }],
                "current-context": "aws",
                "kind": "Config",
                "users": [{
                    "name": "aws",
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1alpha1",
                            "command": "aws",
                            "args": ["eks", "get-token", "--cluster-name", cluster_name],
                        }
                    }
                }]
            }
            return json.dumps(kubeconfig)

        kubeconfig = Output.all(
            cluster.name,
            cluster.endpoint,
            cluster.certificate_authority.data,
        ).apply(lambda args: kubeconfig_args(*args))
        return kubeconfig
    except Exception as e:
        log.error(f"Kubeconfig generation failed: {e}")
        raise


kubeconfig = generate_kubeconfig(eks_cluster)

# Kubernetes Provider
k8s_provider = k8s.Provider(
    "k8s-provider",
    kubeconfig=kubeconfig,
    opts=ResourceOptions(depends_on=[node_group]),
)

# Observability Integration (Fluent Bit)
def deploy_fluent_bit() -> None:
    """Deploy Fluent Bit for log forwarding."""
    try:
        namespace = k8s.core.v1.Namespace(
            "fluent-bit-namespace",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="fluent-bit"
            ),
            opts=ResourceOptions(provider=k8s_provider),
        )

        config_map = k8s.core.v1.ConfigMap(
            "fluent-bit-config",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                namespace=namespace.metadata["name"],
                name="fluent-bit-config",
            ),
            data={
                "fluent-bit.conf": f"""
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info
    Parsers_File parsers.conf

[INPUT]
    Name       tail
    Path       /var/log/containers/*.log
    Parser     docker
    Tag        kube.*
    Refresh_Interval 5

[FILTER]
    Name        kubernetes
    Match       kube.*
    Merge_Log   On
    K8S-Logging.Parser On
    K8S-Logging.Exclude On

[OUTPUT]
    Name   cloudwatch_logs
    Match  kube.*
    region {eks_config.region}
    log_group_name /aws/eks/fluent-bit-cloudwatch
    log_stream_prefix from-fluent-bit-
    auto_create_group true
""",
                "parsers.conf": """
[PARSER]
    Name         docker
    Format       json
    Time_Key     time
    Time_Format  %Y-%m-%dT%H:%M:%S.%L
    Time_Keep    On
"""
            },
            opts=ResourceOptions(provider=k8s_provider),
        )

        service_account = k8s.core.v1.ServiceAccount(
            "fluent-bit-service-account",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                namespace=namespace.metadata["name"],
                name="fluent-bit",
            ),
            opts=ResourceOptions(provider=k8s_provider),
        )

        # ClusterRole
        cluster_role = k8s.rbac.v1.ClusterRole(
            "fluent-bit-cluster-role",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="fluent-bit-read",
            ),
            rules=[
                k8s.rbac.v1.PolicyRuleArgs(
                    api_groups=[""],
                    resources=["namespaces", "pods"],
                    verbs=["get", "list", "watch"],
                )
            ],
            opts=ResourceOptions(provider=k8s_provider),
        )

        # ClusterRoleBinding
        cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
            "fluent-bit-cluster-role-binding",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="fluent-bit-read",
            ),
            subjects=[
                k8s.rbac.v1.SubjectArgs(
                    kind="ServiceAccount",
                    name=service_account.metadata["name"],
                    namespace=namespace.metadata["name"],
                )
            ],
            role_ref=k8s.rbac.v1.RoleRefArgs(
                kind="ClusterRole",
                name=cluster_role.metadata["name"],
                api_group="rbac.authorization.k8s.io",
            ),
            opts=ResourceOptions(provider=k8s_provider),
        )

        # DaemonSet
        daemon_set = k8s.apps.v1.DaemonSet(
            "fluent-bit-daemonset",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                namespace=namespace.metadata["name"],
                name="fluent-bit",
                labels={"app": "fluent-bit"},
            ),
            spec=k8s.apps.v1.DaemonSetSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "fluent-bit"}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "fluent-bit"}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        service_account_name=service_account.metadata["name"],
                        termination_grace_period_seconds=10,
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="fluent-bit",
                                image="amazon/aws-for-fluent-bit:latest",
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    limits={"memory": "200Mi"},
                                    requests={"cpu": "100m", "memory": "100Mi"},
                                ),
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="varlog", mount_path="/var/log"
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="varlibdockercontainers",
                                        mount_path="/var/lib/docker/containers",
                                        read_only=True,
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="config",
                                        mount_path="/fluent-bit/etc/fluent-bit.conf",
                                        sub_path="fluent-bit.conf",
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="config",
                                        mount_path="/fluent-bit/etc/parsers.conf",
                                        sub_path="parsers.conf",
                                    ),
                                ],
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="varlog",
                                host_path=k8s.core.v1.HostPathVolumeSourceArgs(
                                    path="/var/log"
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="varlibdockercontainers",
                                host_path=k8s.core.v1.HostPathVolumeSourceArgs(
                                    path="/var/lib/docker/containers"
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="config",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name=config_map.metadata["name"]
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            opts=ResourceOptions(provider=k8s_provider),
        )

    except Exception as e:
        log.error(f"Failed to deploy Fluent Bit: {e}")
        raise


deploy_fluent_bit()

# Export outputs
pulumi.export("cluster_endpoint", eks_cluster.endpoint)
pulumi.export("cluster_name", eks_cluster.name)
pulumi.export("nodegroup_name", node_group.node_group_name)
pulumi.export("kubeconfig", kubeconfig)
