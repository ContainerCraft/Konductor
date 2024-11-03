import base64
import json
import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native
import pulumi_kubernetes as k8s

# Get the current Pulumi stack name
stack_name = pulumi.get_stack()

# Load configuration values
config = pulumi.Config()

# VPC Configuration
vpc_cidr = config.get("vpc_cidr") or "10.0.0.0/16"

# Allowed SSH CIDR (replace with your IP range)
allowed_ssh_cidr = config.get("allowed_ssh_cidr") or "203.0.113.0/24"  # Example IP range

# EKS Cluster Configuration
eks_cluster_name = config.get("eks_cluster_name") or f"eks-cluster-{stack_name}"
nodegroup_name = config.get("nodegroup_name") or f"nodegroup-{stack_name}"
desired_capacity = config.get_int("desired_capacity") or 2
min_size = config.get_int("min_size") or 1
max_size = config.get_int("max_size") or 3
instance_type = config.get("instance_type") or "t3.medium"
ssh_key_name = config.require("ssh_key_name")

# IAM Roles
eks_role_name = config.get("eks_role_name") or f"eksRole-{stack_name}"
node_role_name = config.get("node_role_name") or f"nodeRole-{stack_name}"

# Retrieve Availability Zones
azs = aws.get_availability_zones(state="available").names[:3]

# Create IAM role for EKS Cluster
eks_role = aws_native.iam.Role(f"eksRole-{stack_name}",
    assume_role_policy_document=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "eks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
        "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
    ],
    role_name=eks_role_name,
)

# Create IAM role for EKS Node Group
node_role = aws_native.iam.Role(f"nodeRole-{stack_name}",
    assume_role_policy_document=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
        "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    ],
    role_name=node_role_name,
)

# Create VPC
vpc = aws_native.ec2.VPC(f"vpc-{stack_name}",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"vpc-{stack_name}"
    )]
)

# Create Internet Gateway
igw = aws_native.ec2.InternetGateway(f"igw-{stack_name}",
    vpc_id=vpc.id,
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"igw-{stack_name}"
    )]
)

# Create Elastic IP for NAT Gateway
nat_eip = aws_native.ec2.EIP(f"natEip-{stack_name}",
    domain="vpc",
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"natEip-{stack_name}"
    )]
)

# Create Subnets across multiple AZs
public_subnets = []
private_subnets = []

for i, az in enumerate(azs):
    public_subnet = aws_native.ec2.Subnet(f"publicSubnet-{stack_name}-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i}.0/24",
        map_public_ip_on_launch=True,
        availability_zone=az,
        tags=[aws_native.ec2.TagArgs(
            key="Name",
            value=f"publicSubnet-{stack_name}-{i}"
        )]
    )
    public_subnets.append(public_subnet)

    private_subnet = aws_native.ec2.Subnet(f"privateSubnet-{stack_name}-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i+10}.0/24",
        map_public_ip_on_launch=False,
        availability_zone=az,
        tags=[aws_native.ec2.TagArgs(
            key="Name",
            value=f"privateSubnet-{stack_name}-{i}"
        )]
    )
    private_subnets.append(private_subnet)

# Create NAT Gateway
nat_gateway = aws_native.ec2.NatGateway(f"natGateway-{stack_name}",
    subnet_id=public_subnets[0].id,
    allocation_id=nat_eip.allocation_id,
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"natGateway-{stack_name}"
    )]
)

# Create Route Tables
public_route_table = aws_native.ec2.RouteTable(f"publicRouteTable-{stack_name}",
    vpc_id=vpc.id,
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"publicRouteTable-{stack_name}"
    )]
)

private_route_table = aws_native.ec2.RouteTable(f"privateRouteTable-{stack_name}",
    vpc_id=vpc.id,
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"privateRouteTable-{stack_name}"
    )]
)

# Create Routes
public_route = aws_native.ec2.Route(f"publicRoute-{stack_name}",
    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id,
)

private_route = aws_native.ec2.Route(f"privateRoute-{stack_name}",
    route_table_id=private_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id,
)

# Associate Subnets with Route Tables
for i, subnet in enumerate(public_subnets):
    aws_native.ec2.SubnetRouteTableAssociation(f"publicSubnetRouteTableAssociation-{stack_name}-{i}",
        subnet_id=subnet.id,
        route_table_id=public_route_table.id
    )

for i, subnet in enumerate(private_subnets):
    aws_native.ec2.SubnetRouteTableAssociation(f"privateSubnetRouteTableAssociation-{stack_name}-{i}",
        subnet_id=subnet.id,
        route_table_id=private_route_table.id
    )

# Create Security Groups
cluster_security_group = aws_native.ec2.SecurityGroup(f"clusterSecurityGroup-{stack_name}",
    vpc_id=vpc.id,
    group_description="EKS cluster security group",
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"clusterSecurityGroup-{stack_name}"
    )]
)

node_security_group = aws_native.ec2.SecurityGroup(f"nodeSecurityGroup-{stack_name}",
    vpc_id=vpc.id,
    group_description="EKS node group security group",
    tags=[aws_native.ec2.TagArgs(
        key="Name",
        value=f"nodeSecurityGroup-{stack_name}"
    )]
)

# Security Group Rules
aws_native.ec2.SecurityGroupIngress(f"nodeToClusterAPIServer-{stack_name}",
    group_id=cluster_security_group.id,
    ip_protocol="tcp",
    from_port=443,
    to_port=443,
    source_security_group_id=node_security_group.id
)

aws_native.ec2.SecurityGroupEgress(f"clusterToNodeGroup-{stack_name}",
    group_id=cluster_security_group.id,
    ip_protocol="tcp",
    from_port=1025,
    to_port=65535,
    destination_security_group_id=node_security_group.id
)

aws_native.ec2.SecurityGroupIngress(f"clusterToNodeGroupIngress-{stack_name}",
    group_id=node_security_group.id,
    ip_protocol="-1",
    from_port=0,
    to_port=0,
    source_security_group_id=cluster_security_group.id
)

aws_native.ec2.SecurityGroupIngress(f"nodeToNodeIngress-{stack_name}",
    group_id=node_security_group.id,
    ip_protocol="-1",
    from_port=0,
    to_port=0,
    source_security_group_id=node_security_group.id
)

# Allow SSH access to nodes (restricted CIDR)
aws_native.ec2.SecurityGroupIngress(f"sshAccess-{stack_name}",
    group_id=node_security_group.id,
    ip_protocol="tcp",
    from_port=22,
    to_port=22,
    cidr_ip=allowed_ssh_cidr
)

# Create KMS Key for EKS Secrets Encryption
kms_key = aws_native.kms.Key(f"kmsKey-{stack_name}",
    description="KMS key for EKS secrets encryption",
    enable_key_rotation=True
)

# Create EKS Cluster with Secrets Encryption and Private Endpoint
eks_cluster = aws_native.eks.Cluster(f"eksCluster-{stack_name}",
    name=eks_cluster_name,
    role_arn=eks_role.arn,
    version="1.26",
    encryption_config=[aws_native.eks.ClusterEncryptionConfigArgs(
        provider=aws_native.eks.ProviderArgs(
            key_arn=kms_key.key_arn
        ),
        resources=["secrets"]
    )],
    resources_vpc_config=aws_native.eks.ClusterResourcesVpcConfigArgs(
        subnet_ids=[subnet.id for subnet in private_subnets],
        security_group_ids=[cluster_security_group.id],
        endpoint_public_access=False,
        endpoint_private_access=True
    ),
    enabled_cluster_log_types=["api", "audit", "authenticator", "controllerManager", "scheduler"],
    tags=[aws_native.eks.ClusterTagArgs(
        key="Name",
        value=eks_cluster_name
    )]
)

# Create EKS Node Group
node_group = aws_native.eks.Nodegroup(f"nodeGroup-{stack_name}",
    cluster_name=eks_cluster.name,
    node_role=node_role.arn,
    subnets=[subnet.id for subnet in private_subnets],
    nodegroup_name=nodegroup_name,
    scaling_config=aws_native.eks.NodegroupScalingConfigArgs(
        desired_size=desired_capacity,
        min_size=min_size,
        max_size=max_size,
    ),
    instance_types=[instance_type],
    remote_access=aws_native.eks.NodegroupRemoteAccessArgs(
        ec2_ssh_key=ssh_key_name,
        source_security_groups=[node_security_group.id],
    ),
    tags=[aws_native.eks.NodegroupTagArgs(
        key="Name",
        value=nodegroup_name
    )]
)

# Create VPC Flow Logs
flow_logs_role = aws_native.iam.Role(f"vpcFlowLogsRole-{stack_name}",
    assume_role_policy_document=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
    ],
)

flow_log_group = aws_native.logs.LogGroup(f"vpcFlowLogGroup-{stack_name}",
    log_group_name=f"/aws/vpc/flowlogs/{vpc.id}",
    retention_in_days=90,
    tags=[aws_native.logs.LogGroupTagArgs(
        key="Name",
        value=f"vpcFlowLogGroup-{stack_name}"
    )]
)

vpc_flow_log = aws_native.ec2.FlowLog(f"vpcFlowLog-{stack_name}",
    resource_id=vpc.id,
    resource_type="VPC",
    traffic_type="ALL",
    log_destination_type="cloud-watch-logs",
    log_group_name=flow_log_group.name,
    deliver_logs_permission_arn=flow_logs_role.arn
)

# Generate Kubeconfig
def generate_kubeconfig(cluster_name, cluster_endpoint, cluster_certificate_authority):
    kubeconfig = {
        "apiVersion": "v1",
        "clusters": [{
            "cluster": {
                "server": cluster_endpoint,
                "certificate-authority-data": cluster_certificate_authority,
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
        "preferences": {},
        "users": [{
            "name": "aws",
            "user": {
                "exec": {
                    "apiVersion": "client.authentication.k8s.io/v1beta1",
                    "command": "aws",
                    "args": ["eks", "get-token", "--cluster-name", cluster_name],
                }
            }
        }]
    }
    return kubeconfig

# Export Kubeconfig
kubeconfig = pulumi.Output.all(
    eks_cluster.name,
    eks_cluster.endpoint,
    eks_cluster.certificate_authority
).apply(lambda args: generate_kubeconfig(
    args[0],
    args[1],
    base64.b64decode(args[2]['data']).decode('utf-8')
))

# Create Kubernetes Provider
k8s_provider = k8s.Provider(f"k8sProvider-{stack_name}",
    kubeconfig=kubeconfig
)

# Deploy Fluent Bit DaemonSet for Application Logging
fluent_bit_manifest = {
    "apiVersion": "v1",
    "kind": "Namespace",
    "metadata": {"name": "logging"}
}

fluent_bit_namespace = k8s.core.v1.Namespace("fluent-bit-namespace",
    metadata=fluent_bit_manifest["metadata"],
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Fluent Bit DaemonSet and ConfigMap
fluent_bit_config_map = k8s.core.v1.ConfigMap("fluent-bit-config",
    metadata={
        "name": "fluent-bit-config",
        "namespace": "logging"
    },
    data={
        "fluent-bit.conf": """
[SERVICE]
    Daemon Off
    Flush 1
    Log_Level info
    Parsers_File parsers.conf

[INPUT]
    Name tail
    Path /var/log/containers/*.log
    Parser docker
    Tag kube.*

[FILTER]
    Name kubernetes
    Match kube.*

[OUTPUT]
    Name cloudwatch_logs
    Match   *
    region  %s
    log_group_name fluent-bit-cloudwatch
    log_stream_prefix from-fluent-bit-
    auto_create_group true
""" % aws.config.region,
        "parsers.conf": """
[PARSER]
    Name   docker
    Format json
    Time_Key time
    Time_Format %Y-%m-%dT%H:%M:%S.%L
    Time_Keep On
"""
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

fluent_bit_service_account = k8s.core.v1.ServiceAccount("fluent-bit-sa",
    metadata={
        "name": "fluent-bit",
        "namespace": "logging"
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

fluent_bit_cluster_role = k8s.rbac.v1.ClusterRole("fluent-bit-cluster-role",
    metadata={"name": "fluent-bit-read"},
    rules=[{
        "apiGroups": [""],
        "resources": ["namespaces", "pods"],
        "verbs": ["get", "list", "watch"]
    }],
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

fluent_bit_cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding("fluent-bit-cluster-role-binding",
    metadata={"name": "fluent-bit-read"},
    subjects=[{
        "kind": "ServiceAccount",
        "name": "fluent-bit",
        "namespace": "logging"
    }],
    role_ref={
        "kind": "ClusterRole",
        "name": "fluent-bit-read",
        "apiGroup": "rbac.authorization.k8s.io"
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

fluent_bit_daemonset = k8s.apps.v1.DaemonSet("fluent-bit-daemonset",
    metadata={
        "name": "fluent-bit",
        "namespace": "logging",
        "labels": {"k8s-app": "fluent-bit-logging"}
    },
    spec={
        "selector": {"matchLabels": {"k8s-app": "fluent-bit-logging"}},
        "template": {
            "metadata": {"labels": {"k8s-app": "fluent-bit-logging"}},
            "spec": {
                "serviceAccountName": "fluent-bit",
                "tolerations": [{"operator": "Exists"}],
                "containers": [{
                    "name": "fluent-bit",
                    "image": "amazon/aws-for-fluent-bit:latest",
                    "resources": {
                        "limits": {"memory": "200Mi"},
                        "requests": {"cpu": "100m", "memory": "100Mi"}
                    },
                    "volumeMounts": [
                        {"name": "varlog", "mountPath": "/var/log"},
                        {"name": "varlibdockercontainers", "mountPath": "/var/lib/docker/containers", "readOnly": True},
                        {"name": "config", "mountPath": "/fluent-bit/etc/fluent-bit.conf", "subPath": "fluent-bit.conf"},
                        {"name": "config", "mountPath": "/fluent-bit/etc/parsers.conf", "subPath": "parsers.conf"},
                    ]
                }],
                "volumes": [
                    {"name": "varlog", "hostPath": {"path": "/var/log"}},
                    {"name": "varlibdockercontainers", "hostPath": {"path": "/var/lib/docker/containers"}},
                    {"name": "config", "configMap": {"name": "fluent-bit-config"}}
                ]
            }
        }
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Export outputs
pulumi.export("cluster_endpoint", eks_cluster.endpoint)
pulumi.export("cluster_name", eks_cluster.name)
pulumi.export("nodegroup_name", node_group.nodegroup_name)
pulumi.export("kubeconfig", kubeconfig)
