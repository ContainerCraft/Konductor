import pulumi
import pulumi_gcp as gcp
from pulumi import log

# Fetch GCP configuration parameters
config = pulumi.Config()
gcp_project = config.require("project")
gcp_region = config.require("region")

log.info(f"Deploying to GCP Project: {gcp_project} in Region: {gcp_region}")

# Create a GCP bucket
bucket = gcp.storage.Bucket(
    "exampleBucket",
    location=gcp_region,
    uniform_bucket_level_access=True,
    labels={"Environment": "Dev", "Name": "MyGCSBucket"}
)

# Get current GCP account information
broker = gcp.organizations.get_broker_project()

# Export the bucket name and broker project information
pulumi.export("bucket_name", bucket.name)
pulumi.export("broker_project_id", broker.project_id)
pulumi.export("broker_project_number", broker.project_number)
pulumi.export("broker_project_ancestry", broker.ancestry)
