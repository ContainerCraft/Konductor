# ./modules/aws/eks/deployment.py
"""EKS cluster deployment management."""

from typing import Dict, List, Optional, Any
import pulumi_aws as aws
import pulumi_kubernetes as k8s
from pulumi import ResourceOptions, log, CustomTimeouts, Output
import json

from .iam import IamRoleManager
from .networking import NetworkManager
from ..types.components.eks import EksConfig, ClusterConfig, NodeGroupConfig


class EksManager:
    """Manages AWS EKS cluster and related resources."""

    def __init__(self, provider):
        self.provider = provider
        self.iam_manager = IamRoleManager(provider)
        self.network_manager = NetworkManager(provider)

    def create_cluster(
        self,
        config: ClusterConfig,
        cluster_role: aws.iam.Role,
        vpc: aws.ec2.Vpc,
        depends_on: Optional[List[Any]] = None,
    ) -> aws.eks.Cluster:
        """Create the EKS cluster control plane."""
        merged_tags = {**self.provider.get_tags(), **(config.tags or {})}

        cluster = aws.eks.Cluster(
            f"eks-{config.name}",
            name=config.name,
            role_arn=cluster_role.arn,
            version=config.version,
            vpc_config=aws.eks.ClusterVpcConfigArgs(
                subnet_ids=config.subnet_ids,
                endpoint_private_access=config.endpoint_private_access,
                endpoint_public_access=config.endpoint_public_access,
            ),
            tags=merged_tags,
            opts=ResourceOptions(
                provider=self.provider.provider,
                depends_on=depends_on,
                parent=vpc,
                custom_timeouts=CustomTimeouts(create="1200s", update="900s", delete="600s"),
            ),
        )

        return cluster

    def create_node_group(
        self,
        config: NodeGroupConfig,
        cluster: aws.eks.Cluster,
        node_role: aws.iam.Role,
    ) -> aws.eks.NodeGroup:
        """Create an EKS node group."""
        merged_tags = {**self.provider.get_tags(), **(config.tags or {})}

        node_group = Output.all(cluster_name=cluster.name).apply(
            lambda args: aws.eks.NodeGroup(
                # Resource name (for Pulumi)
                f"ng-{args['cluster_name']}-{config.name}",
                # Actual AWS node group name (must be <=63 chars)
                node_group_name=f"ng-{config.name}",
                cluster_name=args['cluster_name'],
                node_role_arn=node_role.arn,
                subnet_ids=config.subnet_ids,
                instance_types=config.instance_types,
                scaling_config=aws.eks.NodeGroupScalingConfigArgs(**config.scaling_config),
                tags={
                    **merged_tags,
                    "Name": f"ng-{args['cluster_name']}-{config.name}",
                    "ClusterName": args['cluster_name'],
                    "NodeGroupName": config.name,
                },
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=cluster,
                    custom_timeouts=CustomTimeouts(create="5m", update="5m", delete="15m"),
                ),
            )
        )

        return node_group

    def deploy_clusters(self, eks_config: EksConfig) -> Dict[str, Dict[str, Any]]:
        """Deploy multiple EKS clusters based on configuration."""
        clusters = {}
        for cluster_config in eks_config.clusters:
            log.info(f"Deploying EKS cluster: {cluster_config.name}")
            try:
                result = self.deploy_cluster(
                    name=cluster_config.name,
                    version=cluster_config.version,
                    node_groups=cluster_config.node_groups,
                )
                clusters[cluster_config.name] = result
            except Exception as e:
                log.error(f"Failed to deploy cluster {cluster_config.name}: {str(e)}")
                raise
        return clusters

    def deploy_cluster(
        self,
        name: str,
        version: Optional[str] = None,
        node_groups: Optional[List[NodeGroupConfig]] = None,
    ) -> Dict[str, Any]:
        """Deploy a single EKS cluster with all required components."""
        try:
            # Create VPC and networking
            vpc_resources = self.network_manager.create_vpc(name)
            private_subnet_ids = [subnet.id for subnet in vpc_resources["private_subnets"]]

            # Create IAM roles
            cluster_role = self.iam_manager.create_cluster_role(name)
            node_role = self.iam_manager.create_node_role(name)

            # Create cluster using internal config type
            cluster_config = ClusterConfig(
                name=name,
                version=version or "1.29",
                subnet_ids=private_subnet_ids,
                tags=self.provider.get_tags(),
            )

            cluster = self.create_cluster(
                config=cluster_config,
                cluster_role=cluster_role,
                vpc=vpc_resources["vpc"],
                depends_on=[vpc_resources["vpc"]],
            )

            # Deploy node groups
            deployed_node_groups = []
            if not node_groups:
                # Create default node group with cluster-specific name
                node_groups = [NodeGroupConfig(name="default")]  # Keep name simple, will be prefixed in create_node_group

            for ng_config in node_groups:
                node_group_config = NodeGroupConfig(
                    name=ng_config.name,
                    instance_types=ng_config.instance_types,
                    scaling_config=ng_config.scaling_config,
                    subnet_ids=private_subnet_ids,
                    tags=ng_config.tags,
                )

                node_group = self.create_node_group(
                    config=node_group_config,
                    cluster=cluster,
                    node_role=node_role,
                )
                deployed_node_groups.append(node_group)

            # Generate kubeconfig
            kubeconfig = self._generate_kubeconfig(cluster)

            # Create k8s provider
            k8s_provider = k8s.Provider(
                f"k8s-provider-{name}",
                kubeconfig=kubeconfig.apply(json.dumps),
                opts=ResourceOptions(
                    parent=cluster,
                    depends_on=deployed_node_groups
                ),
            )

            # Export kubeconfig
            secret_kubeconfig = Output.secret(kubeconfig)
            Output.all(secret_kubeconfig).apply(lambda args: Output.secret(args[0])).apply(
                lambda k: Output.all(k).apply(lambda x: Output.secret(x[0]))
            )

            # Deploy test nginx pod
            self._deploy_test_nginx(k8s_provider, name)

            return {
                "vpc": vpc_resources["vpc"],
                "public_subnets": vpc_resources["public_subnets"],
                "private_subnets": vpc_resources["private_subnets"],
                "cluster": cluster,
                "node_group": deployed_node_groups,
                "cluster_role": cluster_role,
                "node_role": node_role,
                "kubeconfig": kubeconfig,
                "k8s_provider": k8s_provider,
            }

        except Exception as e:
            log.error(f"Failed to deploy EKS cluster: {str(e)}")
            raise

    def _generate_kubeconfig(self, cluster: aws.eks.Cluster) -> Output:
        """Generate kubeconfig for EKS cluster."""
        return Output.all(
            name=cluster.name,
            endpoint=cluster.endpoint,
            ca=cluster.certificate_authority,
            profile=self.provider.config.profile,
        ).apply(
            lambda args: {
                "apiVersion": "v1",
                "clusters": [
                    {
                        "cluster": {"server": args["endpoint"], "certificate-authority-data": args["ca"]["data"]},
                        "name": "kubernetes",
                    }
                ],
                "contexts": [{"context": {"cluster": "kubernetes", "user": "aws"}, "name": "aws"}],
                "current-context": "aws",
                "kind": "Config",
                "preferences": {},
                "users": [
                    {
                        "name": "aws",
                        "user": {
                            "exec": {
                                "apiVersion": "client.authentication.k8s.io/v1beta1",
                                "command": "aws-iam-authenticator",
                                "args": ["token", "-i", args["name"]],
                                "env": [{"name": "AWS_PROFILE", "value": args["profile"] or "default"}],
                            }
                        },
                    }
                ],
            }
        )

    def _deploy_test_nginx(self, k8s_provider: k8s.Provider, name: str) -> Optional[k8s.core.v1.Pod]:
        """Deploy a test nginx pod to verify cluster functionality."""
        try:
            log.debug(f"Deploying test Nginx pod for cluster {name}")
            return k8s.core.v1.Pod(
                f"nginx-test-{name}",
                metadata={"name": f"nginx-test-{name}", "namespace": "default"},
                spec={"containers": [{"name": "nginx", "image": "nginx:latest", "ports": [{"containerPort": 80}]}]},
                opts=ResourceOptions(
                    provider=k8s_provider,
                    parent=k8s_provider,
                    custom_timeouts={"create": "1m", "delete": "1m"}
                )
            )
        except Exception as e:
            log.error(f"Failed to deploy test Nginx pod: {str(e)}")
            return None
