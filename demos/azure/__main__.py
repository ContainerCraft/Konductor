import pulumi
import pulumi_azure_native as azure_native
from pulumi import log

# --------------------------------------------------------------------------------------
# Azure Authentication Config
# --------------------------------------------------------------------------------------
# pulumi config set --path azure.region eastus
# pulumi config set --secret --path azure.subscription_id YOUR_SUBSCRIPTION_ID
# pulumi config set --secret --path azure.client_id YOUR_CLIENT_ID
# pulumi config set --secret --path azure.client_secret YOUR_CLIENT_SECRET
# pulumi config set --secret --path azure.tenant_id YOUR_TENANT_ID

# --------------------------------------------------------------------------------------
# Initialize Pulumi Configuration
# --------------------------------------------------------------------------------------

# Load the Pulumi configuration for the current stack.
# This configuration is populated via 'pulumi config' commands.
config = pulumi.Config()

# Access the 'azure' configuration object set using the '--path' flag.
# This allows us to read nested configuration values.
# For example, if you set the region using:
#   pulumi config set --path azure.region eastus
# Then you can access it as shown below.
azure_config = config.require_object("azure")

# Fetch the Azure region from the configuration.
azure_region = azure_config.get("region")

# Log the Azure region for visibility during deployment.
log.info(f"Deploying to Azure Region: {azure_region}")

# --------------------------------------------------------------------------------------
# Optional: Fetch Azure Credentials from Configuration
# --------------------------------------------------------------------------------------

# It's generally recommended to manage Azure credentials outside of code and configuration files.
# Credentials can be managed via environment variables or Azure CLI authentication.
# However, for demonstration purposes, we show how to fetch them from Pulumi configuration.

# Fetch Azure credentials from the configuration, if they exist.
azure_subscription_id = azure_config.get("subscription_id")
azure_client_id = azure_config.get("client_id")
azure_client_secret = azure_config.get("client_secret")
azure_tenant_id = azure_config.get("tenant_id")

# --------------------------------------------------------------------------------------
# Create an Azure Provider Instance
# --------------------------------------------------------------------------------------

# Prepare arguments for the Azure provider.
# The provider is responsible for all interactions with Azure services.
azure_provider_args = {
    "location": azure_region,
}

# If credentials are provided in the configuration, include them in the provider arguments.
if azure_subscription_id and azure_client_id and azure_client_secret and azure_tenant_id:
    azure_provider_args.update({
        "subscription_id": azure_subscription_id,
        "client_id": azure_client_id,
        "client_secret": azure_client_secret,
        "tenant_id": azure_tenant_id,
    })
    log.info("Using Azure credentials from Pulumi configuration.")
else:
    log.info("Using default Azure credential methods (e.g., Azure CLI login).")

# Instantiate the Azure provider with the specified arguments.
azure_provider = azure_native.Provider("azure_provider", **azure_provider_args)

# --------------------------------------------------------------------------------------
# Create Azure Resources Using the Provider
# --------------------------------------------------------------------------------------

# Create a Resource Group to hold all other resources.
resource_group = azure_native.resources.ResourceGroup(
    "exampleResourceGroup",
    location=azure_region,
    opts=pulumi.ResourceOptions(provider=azure_provider),
)

# Create an Azure Storage Account using the custom Azure provider.
storage_account = azure_native.storage.StorageAccount(
    "examplestorageaccount",
    resource_group_name=resource_group.name,
    sku=azure_native.storage.SkuArgs(
        name=azure_native.storage.SkuName.STANDARD_LRS,
    ),
    kind=azure_native.storage.Kind.STORAGE_V2,
    location=azure_region,
    tags={"Environment": "Dev", "Name": "MyStorageAccount"},
    opts=pulumi.ResourceOptions(provider=azure_provider),
)

# Create a Blob Container in the Storage Account.
blob_container = azure_native.storage.BlobContainer(
    "examplecontainer",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    public_access=azure_native.storage.PublicAccess.NONE,
    opts=pulumi.ResourceOptions(provider=azure_provider),
)

# --------------------------------------------------------------------------------------
# Retrieve Azure Caller Identity
# --------------------------------------------------------------------------------------

# Use Azure Authorization module to get information about the current caller identity.
# Note: We are not passing the 'opts' parameter here to avoid potential version compatibility issues.
# If you need to use a specific provider, ensure your Pulumi SDK and provider plugins are up-to-date.
import pulumi_azure as azure

identity_output = azure.authorization.get_client_config()

# --------------------------------------------------------------------------------------
# Export Outputs for Visibility
# --------------------------------------------------------------------------------------

# Export the name of the Storage Account and Blob Container for easy access after deployment.
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("blob_container_name", blob_container.name)

# Export the caller identity information for auditing and verification purposes.
pulumi.export("caller_identity_client_id", identity_output.client_id)
pulumi.export("caller_identity_object_id", identity_output.object_id)
pulumi.export("caller_identity_tenant_id", identity_output.tenant_id)
