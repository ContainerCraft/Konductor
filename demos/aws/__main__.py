import pulumi
import pulumi_aws as aws
from pulumi import log

# --------------------------------------------------------------------------------------
# Initialize Pulumi Configuration
# --------------------------------------------------------------------------------------

# Load the Pulumi configuration for the current stack.
# This configuration is populated via 'pulumi config' commands.
config = pulumi.Config()

# Access the 'aws' configuration object set using the '--path' flag.
# This allows us to read nested configuration values.
# For example, if you set the region using:
#   pulumi config set --path aws.region us-east-1
# Then you can access it as shown below.
aws_config = config.require_object("aws")

# Fetch the AWS region from the configuration.
aws_region = aws_config.get("region")

# Log the AWS region for visibility during deployment.
log.info(f"Deploying to AWS Region: {aws_region}")

# --------------------------------------------------------------------------------------
# Optional: Fetch AWS Credentials from Configuration
# -------------------------------------------------------------------------------------

# It's generally recommended to manage AWS credentials outside of code and configuration files.
# Credentials can be managed via environment variables, AWS profiles, or secret management systems.
# However, for demonstration purposes, we show how to fetch them from Pulumi configuration.

# Fetch AWS credentials from the configuration, if they exist.
aws_access_key_id = aws_config.get("access_key_id")
aws_secret_access_key = aws_config.get("secret_access_key")

# -------------------------------------------------------------------------------------
# Create an AWS Provider Instance
# -------------------------------------------------------------------------------------

# Prepare arguments for the AWS provider.
# The provider is responsible for all interactions with AWS services.
aws_provider_args = {"region": aws_region}

# If credentials are provided in the configuration, include them in the provider arguments.
if aws_access_key_id and aws_secret_access_key:
    aws_provider_args.update(
        {"access_key": aws_access_key_id, "secret_key": aws_secret_access_key}
    )
    log.info("Using AWS credentials from Pulumi configuration.")
else:
    log.info(
        "Using default AWS credential methods (e.g., environment variables, AWS profiles)."
    )

# Instantiate the AWS provider with the specified arguments.
aws_provider = aws.Provider("aws_provider", **aws_provider_args)

# --------------------------------------------------------------------------------------
# Create AWS Resources Using the Provider
# --------------------------------------------------------------------------------------

# Create an Amazon S3 bucket using the custom AWS provider.
s3_bucket = aws.s3.Bucket(
    "exampleBucket",
    acl="private",
    tags={"Environment": "Dev", "Name": "MyS3Bucket"},
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# --------------------------------------------------------------------------------------
# Retrieve AWS Caller Identity
# --------------------------------------------------------------------------------------

# Use AWS STS (Security Token Service) to get information about the current caller identity.
# Note: We are not passing the 'opts' parameter here to avoid potential version compatibility issues.
# If you need to use a specific provider, ensure your Pulumi SDK and provider plugins are up-to-date.
caller_identity = aws.get_caller_identity(
    opts=pulumi.InvokeOptions(provider=aws_provider)
)

# --------------------------------------------------------------------------------------
# Export Outputs for Visibility
# --------------------------------------------------------------------------------------

# Export the name of the S3 bucket for easy access after deployment.
pulumi.export("s3_bucket_name", s3_bucket.bucket)

# Export AWS caller identity details for auditing and verification purposes.
pulumi.export("caller_identity_account", caller_identity.account_id)
pulumi.export("caller_identity_arn", caller_identity.arn)
pulumi.export("caller_identity_user_id", caller_identity.user_id)
