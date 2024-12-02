import pulumi
import pulumi_openstack as openstack
from pulumi import log

# --------------------------------------------------------------------------------------
# OpenStack Authentication Configuration
# --------------------------------------------------------------------------------------
# pulumi config set --path openstack.auth_url https://your-openstack-auth-url
# pulumi config set --secret --path openstack.username YOUR_USERNAME
# pulumi config set --secret --path openstack.password YOUR_PASSWORD
# pulumi config set --path openstack.tenant_name YOUR_TENANT_NAME
# pulumi config set --path openstack.region YOUR_REGION

# --------------------------------------------------------------------------------------
# Initialize Pulumi Configuration
# --------------------------------------------------------------------------------------

# Load the Pulumi configuration for the current stack.
# This configuration is populated via 'pulumi config' commands.
config = pulumi.Config()

# Access the 'openstack' configuration object set using the '--path' flag.
# This allows us to read nested configuration values.
# For example, if you set the auth_url using:
#   pulumi config set --path openstack.auth_url https://your-openstack-auth-url
# Then you can access it as shown below.
openstack_config = config.require_object("openstack")

# Fetch OpenStack credentials and region from the configuration.
auth_url = openstack_config.get("auth_url")
username = openstack_config.get("username")
password = openstack_config.get("password")
tenant_name = openstack_config.get("tenant_name")
region = openstack_config.get("region")

# Log the OpenStack region for visibility during deployment.
log.info(f"Deploying to OpenStack Region: {region}")

# --------------------------------------------------------------------------------------
# Optional: Fetch OpenStack Credentials from Configuration
# --------------------------------------------------------------------------------------

# It's generally recommended to manage OpenStack credentials outside of code and configuration files.
# Credentials can be managed via environment variables or secret management systems.
# However, for demonstration purposes, we show how to fetch them from Pulumi configuration.

# Check if all required credentials are provided.
credentials_provided = all([auth_url, username, password, tenant_name])

# --------------------------------------------------------------------------------------
# Create an OpenStack Provider Instance
# --------------------------------------------------------------------------------------

# Prepare arguments for the OpenStack provider.
# The provider is responsible for all interactions with OpenStack services.
openstack_provider_args = {"region": region}

# If credentials are provided in the configuration, include them in the provider arguments.
if credentials_provided:
    openstack_provider_args.update({
        "auth_url": auth_url,
        "user_name": username,
        "password": password,
        "tenant_name": tenant_name,
    })
    log.info("Using OpenStack credentials from Pulumi configuration.")
else:
    log.info("Using default OpenStack credential methods (e.g., environment variables).")

# Instantiate the OpenStack provider with the specified arguments.
openstack_provider = openstack.Provider("openstack_provider", **openstack_provider_args)

# --------------------------------------------------------------------------------------
# Create OpenStack Resources Using the Provider
# --------------------------------------------------------------------------------------

# Create an OpenStack Object Storage Container using the custom OpenStack provider.
storage_container = openstack.objectstorage.Container(
    "exampleContainer",
    opts=pulumi.ResourceOptions(provider=openstack_provider),
)

# --------------------------------------------------------------------------------------
# Retrieve OpenStack Authenticated User Identity
# --------------------------------------------------------------------------------------

# Use OpenStack Identity service to get information about the current authenticated user.
authenticated_user = openstack.identity.get_authenticated_user(
    opts=pulumi.InvokeOptions(provider=openstack_provider)
)

# --------------------------------------------------------------------------------------
# Export Outputs for Visibility
# --------------------------------------------------------------------------------------

# Export the name of the storage container for easy access after deployment.
pulumi.export("storage_container_name", storage_container.name)

# Export OpenStack authenticated user details for auditing and verification purposes.
pulumi.export("authenticated_user_id", authenticated_user.user_id)
pulumi.export("authenticated_user_name", authenticated_user.user_name)
pulumi.export("authenticated_user_domain_id", authenticated_user.domain_id)
