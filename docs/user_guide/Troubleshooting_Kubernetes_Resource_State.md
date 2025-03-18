# Resolving Kubernetes Cluster State Issues with Pulumi

## Introduction

This document provides a step-by-step guide to resolving issues when Pulumi fails to destroy unreachable Kubernetes resources. It follows the Konductor project’s documentation standards and aligns with Pulumi Python development best practices.

This guide is designed to assist developers in handling errors related to `PULUMI_K8S_DELETE_UNREACHABLE` and Kubernetes provider misconfigurations. By following these steps, you can ensure smooth and complete infrastructure teardown, avoiding unnecessary cloud costs.

## Troubleshooting Steps

### 1. Identify the Problematic Resource

To identify Kubernetes resources causing destroy failures:

1. Export the Pulumi stack state:

   ```bash
   pulumi stack export > stack.json
   ```

2. Use `jq` to filter Kubernetes resources:

   ```bash
   cat stack.json | jq '.deployment.resources[] | select(.type == "kubernetes:core/v1:Pod") | .urn'
   ```

   **Example Output:**

   ```
   "urn:pulumi:navteca-aws-credentials-config-smce::konductor::kubernetes:core/v1:Pod::nginx-test-test-eks-cluster"
   ```

### 2. Use `PULUMI_K8S_DELETE_UNREACHABLE`

Set the environment variable to allow deletion of unreachable resources:

1. Export the variable:

   ```bash
   export PULUMI_K8S_DELETE_UNREACHABLE=true
   ```

2. Attempt to destroy the resource:

   ```bash
   pulumi destroy --target="urn:<resource-URN>" --refresh --skip-preview
   ```

   If the operation fails, proceed to manually remove the resource from the state.

### 3. Manually Remove the Resource

1. Delete the resource directly from the Pulumi state:

   ```bash
   pulumi state delete "urn:<resource-URN>"
   ```

   **Example:**

   ```bash
   pulumi state delete "urn:pulumi:navteca-aws-credentials-config-smce::konductor::kubernetes:core/v1:Pod::nginx-test-test-eks-cluster"
   ```

2. Retry the destroy operation for the entire stack:

   ```bash
   pulumi destroy --skip-preview --refresh --continue-on-error
   ```

### 4. Validate and Clean Up

1. Ensure all resources have been deleted by reviewing the destroy output.
2. Remove the Pulumi stack if no longer needed:

   ```bash
   pulumi stack rm <stack-name>
   ```

## Best Practices

### Handling Kubernetes Resources

- **Use `PULUMI_K8S_DELETE_UNREACHABLE` Proactively:** Set the environment variable when working with ephemeral or potentially inaccessible clusters.
- **Monitor Resource Dependencies:** Use `depends_on` in Pulumi to manage resource creation and deletion order.
- **Backup Pulumi State:** Export the stack state regularly:

  ```bash
  pulumi stack export > backup-<date>.json
  ```

### Configurations

- **Namespace Management:** Explicitly set namespaces for Kubernetes resources to avoid conflicts.
- **Pulumi Provider Configuration:** Ensure the Kubernetes provider is properly configured with an accessible kubeconfig file:

  ```python
  k8s_provider = pulumi_kubernetes.Provider(
      "k8s-provider",
      kubeconfig="~/.kube/config"
  )
  ```

### Debugging

- **Use Pulumi’s debug logging to analyze failures:**

  ```bash
  pulumi destroy --debug --skip-preview
  ```

## Common Errors and Solutions

| Error Message                                        | Cause                                                | Solution                                                                 |
|------------------------------------------------------|------------------------------------------------------|--------------------------------------------------------------------------|
| configured Kubernetes cluster is unreachable          | Cluster is deleted or unreachable.                   | Use `PULUMI_K8S_DELETE_UNREACHABLE` or manually remove the resource.     |
| failed to read resource state due to unreachable API | Pulumi cannot reconcile the resource state.          | Manually delete the resource using `pulumi state delete`.                |
| preview failed: unable to load schema information    | Invalid or missing Kubernetes provider configuration. | Check and update the kubeconfig path in the Pulumi provider configuration. |
| error: update failed                                 | Failed to delete a dependent resource.               | Identify and remove dependencies manually from the Pulumi state.         |

## Advanced Techniques

### Recreate a Dummy Cluster

If the original cluster has been deleted but its resources remain in the Pulumi state:

1. Recreate a temporary cluster with the same name and configuration.
2. Retry the destroy operation to clean up the resources.
