# ./modules/aws/deployment.py
from typing import Dict, Any, List
import pulumi
from pulumi import log
import pulumi_aws as aws
from pulumi import ResourceOptions
import json

from modules.core.interfaces import ModuleInterface, ModuleDeploymentResult
from modules.core.types import InitializationConfig
from .provider import AWSProvider
from .types import AWSConfig
from modules.core.stack_outputs import collect_global_metadata, collect_module_metadata
from modules.core.compliance_types import ComplianceConfig
from .eks import EksManager


class AwsModule(ModuleInterface):
    """AWS module implementation."""

    def __init__(self, init_config: InitializationConfig):
        self.name = "aws"
        self.init_config = init_config

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate AWS configuration."""
        try:
            if config is None:
                config = {}

            # Ensure minimum required fields
            config.setdefault("enabled", True)
            config.setdefault("region", "us-east-1")

            AWSConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy AWS infrastructure."""
        try:
            # Access init_config from the instance if necessary
            init_config = self.init_config

            # Ensure we have a valid config dictionary
            if not config:
                config = {}

            # Get AWS configuration from Pulumi config if not provided
            pulumi_config = pulumi.Config()
            aws_config_obj = pulumi_config.get_object("aws") or {}
            config = {**aws_config_obj, **config}

            # Parse and validate config
            aws_config = AWSConfig(**config)

            # Initialize provider
            provider = AWSProvider(aws_config)

            log.info(f"Attempting AWS authentication in region: {provider.region}")

            # Get caller identity to verify credentials
            caller_identity = provider.get_caller_identity()

            # Log success
            log.info(f"Successfully authenticated as: {caller_identity.arn}")
            log.info(f"AWS Account ID: {caller_identity.account_id}")

            # Initialize metadata dict
            aws_metadata = {}
            k8s_provider = None

            # Deploy EKS if enabled
            if aws_config.eks and aws_config.eks.enabled:
                log.info(f"Deploying EKS cluster: {aws_config.eks.name}")
                eks_manager = EksManager(provider)
                eks_resources = eks_manager.deploy_cluster(
                    name=aws_config.eks.name,
                    version=aws_config.eks.version,
                    instance_types=aws_config.eks.node_groups[0].instance_types if aws_config.eks.node_groups else None,
                    scaling_config=aws_config.eks.node_groups[0].scaling_config if aws_config.eks.node_groups else None,
                )

                # Store k8s_provider and EKS info in metadata
                k8s_provider = eks_resources["k8s_provider"]
                aws_metadata["k8s_provider"] = k8s_provider
                aws_metadata["eks_cluster_name"] = aws_config.eks.name

                # Export EKS outputs
                pulumi.export("eks_cluster_name", eks_resources["cluster"].name)
                pulumi.export("eks_cluster_endpoint", eks_resources["cluster"].endpoint)
                pulumi.export("eks_cluster_vpc_id", eks_resources["vpc"].id)

            # Get Git info as dictionary
            # retain this code for now, do not remove
            git_info = init_config.git_info.model_dump()

            # Collect metadata for resource tagging
            global_metadata = collect_global_metadata()

            # Update aws_metadata with caller identity info
            caller_identity = provider.get_caller_identity()
            aws_metadata.update({
                "account_id": caller_identity.account_id,
                "user_id": caller_identity.user_id,
                "arn": caller_identity.arn,
            })

            # Merge with global metadata
            combined_metadata = collect_module_metadata(
                global_metadata=global_metadata,
                modules_metadata={"aws": aws_metadata},
            )

            # Sanitize resource tags
            resource_tags = provider.sanitize_tags({
                "Project": combined_metadata["project_name"],
                "Stack": combined_metadata["stack_name"],
                "GitCommit": combined_metadata.get("commit_hash", ""),
                "AWSAccountID": aws_metadata["account_id"],
                "Compliance:Framework": "NIST",
                "Compliance:Controls": "AC-2, AC-3",
            })

            # Define AWS resources with sanitized tags
            bucket_name = f"konductor-{init_config.stack_name}-{provider.region}"
            s3_bucket = aws.s3.Bucket(
                bucket_name,
                bucket=aws_config.bucket,
                tags=resource_tags,
                opts=ResourceOptions(provider=provider.provider, protect=False, parent=provider.provider),
            )

            # Export outputs
            pulumi.export("aws_s3_bucket_name", s3_bucket.id)

            # Parse compliance config
            compliance_config = ComplianceConfig.model_validate(config.get("compliance", {}))

            # Create IAM role for Crossplane AWS Provider if EKS is enabled
            crossplane_role = None
            if aws_config.eks and aws_config.eks.enabled:
                # Get the OIDC issuer URL and clean it properly
                oidc_url = eks_resources['cluster'].identities[0].oidcs[0].issuer.apply(
                    lambda x: x.removeprefix('https://')
                )

                # Get the OIDC provider ARN
                oidc_provider_arn = pulumi.Output.all(account_id=caller_identity.account_id, url=oidc_url).apply(
                    lambda args: f"arn:aws:iam::{args['account_id']}:oidc-provider/{args['url']}"
                )

                # Create the trust policy with proper formatting
                crossplane_trust_policy = pulumi.Output.all(provider_arn=oidc_provider_arn, url=oidc_url).apply(
                    lambda args: {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Federated": args['provider_arn']
                                },
                                "Action": "sts:AssumeRoleWithWebIdentity",
                                "Condition": {
                                    "StringEquals": {
                                        f"{args['url']}:sub": "system:serviceaccount:crossplane-system:provider-aws",
                                        f"{args['url']}:aud": "sts.amazonaws.com"
                                    }
                                }
                            }
                        ]
                    }
                )

                # Create the IAM role with the fixed trust policy
                crossplane_role = aws.iam.Role(
                    "crossplane-provider-aws",
                    assume_role_policy=pulumi.Output.json_dumps(crossplane_trust_policy),
                    tags=resource_tags,
                    opts=ResourceOptions(
                        provider=provider.provider,
                        depends_on=[eks_resources['cluster']]
                    )
                )

                # Attach required policies
                aws.iam.RolePolicyAttachment(
                    "crossplane-provider-aws-admin",
                    role=crossplane_role.name,
                    policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",  # Note: Consider limiting this in production
                    opts=ResourceOptions(
                        provider=provider.provider,
                        depends_on=[crossplane_role]
                    )
                )

                # Add role ARN to metadata
                aws_metadata["crossplane_provider_role_arn"] = crossplane_role.arn

            # Return deployment result
            return ModuleDeploymentResult(
                success=True,
                version="0.0.1",
                resources=[str(provider.provider.urn), str(s3_bucket.id)],
                metadata={
                    "compliance": compliance_config.model_dump(),
                    "aws_account_id": caller_identity.account_id,
                    "aws_user_id": caller_identity.user_id,
                    "aws_arn": caller_identity.arn,
                    "k8s_provider": k8s_provider if k8s_provider else None,
                    **aws_metadata,
                },
            )

        except Exception as e:
            return ModuleDeploymentResult(
                success=False,
                version="",
                errors=[str(e)]
            )

    def get_dependencies(self) -> List[str]:
        """Get module dependencies."""
        return []
