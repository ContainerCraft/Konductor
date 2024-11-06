# pulumi/modules/aws/resources.py

"""
AWS Resource Management Module

Handles creation and management of AWS resources including:
- S3 buckets and objects
- EC2 instances and volumes
- IAM roles and policies
- VPC and networking components
- Security groups and rules
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

from .types import AWSConfig
from .exceptions import ResourceCreationError
from .security import SecurityManager

if TYPE_CHECKING:
    from .provider import AWSProvider
    from pulumi import Resource

class ResourceManager:
    """
    Manages AWS resources and operations.

    This class handles:
    - Resource creation and configuration
    - Resource tagging and metadata
    - Resource protection settings
    - Resource dependencies
    """

    def __init__(self, provider: 'AWSProvider'):
        """
        Initialize Resource manager.

        Args:
            provider: AWSProvider instance for resource management
        """
        self.provider = provider

    def create_s3_bucket(
        self,
        name: str,
        versioning: bool = True,
        encryption: bool = True,
        public_access_block: bool = True,
        opts: Optional[ResourceOptions] = None
    ) -> aws.s3.Bucket:
        """
        Creates an S3 bucket with standard security configurations.

        Args:
            name: Bucket name
            versioning: Enable versioning
            encryption: Enable encryption
            public_access_block: Block public access
            opts: Optional resource options

        Returns:
            aws.s3.Bucket: Created S3 bucket
        """
        if opts is None:
            opts = ResourceOptions()

        # Create the bucket
        bucket = aws.s3.Bucket(
            name,
            versioning=aws.s3.BucketVersioningArgs(
                enabled=versioning
            ) if versioning else None,
            server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
                rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256"
                    )
                )
            ) if encryption else None,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Block public access if enabled
        if public_access_block:
            aws.s3.BucketPublicAccessBlock(
                f"{name}-public-access-block",
                bucket=bucket.id,
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=bucket,
                    protect=True
                )
            )

        return bucket

    def create_kms_key(
        self,
        name: str,
        description: str,
        deletion_window: int = 30,
        enable_key_rotation: bool = True,
        opts: Optional[ResourceOptions] = None
    ) -> aws.kms.Key:
        """
        Creates a KMS key with standard configuration.

        Args:
            name: Key name
            description: Key description
            deletion_window: Key deletion window in days
            enable_key_rotation: Enable automatic key rotation
            opts: Optional resource options

        Returns:
            aws.kms.Key: Created KMS key
        """
        if opts is None:
            opts = ResourceOptions()

        key = aws.kms.Key(
            name,
            description=description,
            deletion_window_in_days=deletion_window,
            enable_key_rotation=enable_key_rotation,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Create an alias for the key
        aws.kms.Alias(
            f"{name}-alias",
            name=f"alias/{name}",
            target_key_id=key.id,
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=key,
                protect=True
            )
        )

        return key

    def create_cloudwatch_log_group(
        self,
        name: str,
        retention_days: int = 30,
        kms_key_id: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.cloudwatch.LogGroup:
        """
        Creates a CloudWatch Log Group.

        Args:
            name: Log group name
            retention_days: Log retention period
            kms_key_id: Optional KMS key for encryption
            opts: Optional resource options

        Returns:
            aws.cloudwatch.LogGroup: Created log group
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.cloudwatch.LogGroup(
            name,
            retention_in_days=retention_days,
            kms_key_id=kms_key_id,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_sns_topic(
        self,
        name: str,
        kms_master_key_id: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.sns.Topic:
        """
        Creates an SNS topic.

        Args:
            name: Topic name
            kms_master_key_id: Optional KMS key for encryption
            opts: Optional resource options

        Returns:
            aws.sns.Topic: Created SNS topic
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.sns.Topic(
            name,
            kms_master_key_id=kms_master_key_id,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_sqs_queue(
        self,
        name: str,
        visibility_timeout_seconds: int = 30,
        message_retention_seconds: int = 345600,
        kms_master_key_id: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.sqs.Queue:
        """
        Creates an SQS queue.

        Args:
            name: Queue name
            visibility_timeout_seconds: Message visibility timeout
            message_retention_seconds: Message retention period
            kms_master_key_id: Optional KMS key for encryption
            opts: Optional resource options

        Returns:
            aws.sqs.Queue: Created SQS queue
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.sqs.Queue(
            name,
            visibility_timeout_seconds=visibility_timeout_seconds,
            message_retention_seconds=message_retention_seconds,
            kms_master_key_id=kms_master_key_id,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_dynamodb_table(
        self,
        name: str,
        hash_key: str,
        range_key: Optional[str] = None,
        attributes: List[Dict[str, str]] = None,
        billing_mode: str = "PAY_PER_REQUEST",
        opts: Optional[ResourceOptions] = None
    ) -> aws.dynamodb.Table:
        """
        Creates a DynamoDB table.

        Args:
            name: Table name
            hash_key: Partition key name
            range_key: Optional sort key name
            attributes: List of attribute definitions
            billing_mode: Billing mode (PAY_PER_REQUEST or PROVISIONED)
            opts: Optional resource options

        Returns:
            aws.dynamodb.Table: Created DynamoDB table
        """
        if opts is None:
            opts = ResourceOptions()

        if attributes is None:
            attributes = [{"name": hash_key, "type": "S"}]
            if range_key:
                attributes.append({"name": range_key, "type": "S"})

        return aws.dynamodb.Table(
            name,
            attributes=[
                aws.dynamodb.TableAttributeArgs(**attr)
                for attr in attributes
            ],
            hash_key=hash_key,
            range_key=range_key,
            billing_mode=billing_mode,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_ecr_repository(
        self,
        name: str,
        image_tag_mutability: str = "IMMUTABLE",
        scan_on_push: bool = True,
        opts: Optional[ResourceOptions] = None
    ) -> aws.ecr.Repository:
        """
        Creates an ECR repository.

        Args:
            name: Repository name
            image_tag_mutability: Tag mutability setting
            scan_on_push: Enable image scanning on push
            opts: Optional resource options

        Returns:
            aws.ecr.Repository: Created ECR repository
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.ecr.Repository(
            name,
            image_tag_mutability=image_tag_mutability,
            image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                scan_on_push=scan_on_push
            ),
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_backup_vault(
        self,
        name: str,
        kms_key_arn: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.backup.Vault:
        """
        Creates an AWS Backup vault.

        Args:
            name: Vault name
            kms_key_arn: Optional KMS key ARN for encryption
            opts: Optional resource options

        Returns:
            aws.backup.Vault: Created backup vault
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.backup.Vault(
            name,
            kms_key_arn=kms_key_arn,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_backup_plan(
        self,
        name: str,
        vault_name: str,
        schedule: str,
        retention_days: int = 30,
        opts: Optional[ResourceOptions] = None
    ) -> aws.backup.Plan:
        """
        Creates an AWS Backup plan.

        Args:
            name: Plan name
            vault_name: Backup vault name
            schedule: Backup schedule expression
            retention_days: Backup retention period
            opts: Optional resource options

        Returns:
            aws.backup.Plan: Created backup plan
        """
        if opts is None:
            opts = ResourceOptions()

        backup_plan: aws.backup.Plan = aws.backup.Plan(
            name,
            rules=[aws.backup.PlanRuleArgs(
                rule_name=f"{name}-rule",
                target_vault_name=vault_name,
                schedule=schedule,
                lifecycle=aws.backup.PlanRuleLifecycleArgs(
                    delete_after=retention_days
                )
            )],
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        return backup_plan
