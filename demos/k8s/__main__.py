import pulumi
import pulumi_kubernetes as k8s
from pulumi import log

# --------------------------------------------------------------------------------------
# Kubernetes Authentication Configuration
# --------------------------------------------------------------------------------------
# pulumi config set --path k8s.namespace my-namespace
# pulumi config set --path k8s.pvc_name my-pvc
# pulumi config set --path k8s.storage_class_name my-storage-class
# pulumi config set --path k8s.kubeconfig "$(cat ~/.kube/config)"

# --------------------------------------------------------------------------------------
# Initialize Pulumi Configuration
# --------------------------------------------------------------------------------------

# Load the Pulumi configuration for the current stack.
# This configuration is populated via 'pulumi config' commands.
config = pulumi.Config()

# Access the 'k8s' configuration object set using the '--path' flag.
# This allows us to read nested configuration values.
# For example, if you set the namespace using:
#   pulumi config set --path k8s.namespace my-namespace
# Then you can access it as shown below.
k8s_config = config.get_object("k8s") or {}

# Fetch Kubernetes configuration values with defaults.
namespace = k8s_config.get("namespace", "default")
pvc_name = k8s_config.get("pvc_name", "example-pvc")
storage_class_name = k8s_config.get("storage_class_name", "standard")

# Log the Kubernetes namespace for visibility during deployment.
log.info(f"Deploying to Kubernetes Namespace: {namespace}")

# --------------------------------------------------------------------------------------
# Optional: Fetch Kubernetes Context from Configuration
# --------------------------------------------------------------------------------------

# It's generally recommended to manage Kubernetes contexts outside of code and configuration files.
# Contexts can be managed via kubeconfig files or environment variables.
# However, for demonstration purposes, we show how to fetch them from Pulumi configuration.

# Fetch Kubernetes context from the configuration, if it exists.
kubeconfig = config.get("kubeconfig")

# --------------------------------------------------------------------------------------
# Create a Kubernetes Provider Instance
# --------------------------------------------------------------------------------------

# Prepare arguments for the Kubernetes provider.
# The provider is responsible for all interactions with Kubernetes clusters.
k8s_provider_args = {}

# If a kubeconfig is provided in the configuration, include it in the provider arguments.
if kubeconfig:
    k8s_provider_args["kubeconfig"] = kubeconfig
    log.info("Using Kubernetes context from Pulumi configuration.")
else:
    log.info("Using default Kubernetes context (e.g., from KUBECONFIG environment variable or default kubeconfig file).")

# Instantiate the Kubernetes provider with the specified arguments.
k8s_provider = k8s.Provider("k8s_provider", **k8s_provider_args)

# --------------------------------------------------------------------------------------
# Create Kubernetes Resources Using the Provider
# --------------------------------------------------------------------------------------

# Create a Kubernetes Namespace using the custom provider.
namespace_resource = k8s.core.v1.Namespace(
    "example-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=namespace,
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

# Create a Persistent Volume.
persistent_volume = k8s.core.v1.PersistentVolume(
    "example-pv",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="example-pv",
    ),
    spec=k8s.core.v1.PersistentVolumeSpecArgs(
        capacity={"storage": "1Gi"},
        access_modes=["ReadWriteOnce"],
        persistent_volume_reclaim_policy="Retain",
        storage_class_name=storage_class_name,
        nfs=k8s.core.v1.NFSVolumeSourceArgs(
            path="/some/path",
            server="nfs-server.example.com",
        ),
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[namespace_resource],
    ),
)

# Create a Persistent Volume Claim in the specified Namespace.
persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
    "example-pvc",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=pvc_name,
        namespace=namespace,
    ),
    spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
        access_modes=["ReadWriteOnce"],
        resources=k8s.core.v1.ResourceRequirementsArgs(
            requests={"storage": "1Gi"},
        ),
        storage_class_name=storage_class_name,
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[persistent_volume],
    ),
)

# --------------------------------------------------------------------------------------
# Retrieve Kubernetes Cluster Information
# --------------------------------------------------------------------------------------

# Use the Kubernetes provider to get information about the current cluster.
cluster_version = k8s.core.v1.NodeList.get(
    "nodes",
    opts=pulumi.InvokeOptions(provider=k8s_provider),
).items[0].status.node_info.kubelet_version

# --------------------------------------------------------------------------------------
# Export Outputs for Visibility
# --------------------------------------------------------------------------------------

# Export the names of the resources for easy access after deployment.
pulumi.export("namespace", namespace_resource.metadata["name"])
pulumi.export("persistent_volume_name", persistent_volume.metadata["name"])
pulumi.export("persistent_volume_claim_name", persistent_volume_claim.metadata["name"])

# Export Kubernetes cluster information.
pulumi.export("kubernetes_version", cluster_version)
