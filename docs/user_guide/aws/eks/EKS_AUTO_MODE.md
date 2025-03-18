# AWS EKS Auto Mode

This guide explains how the Zora AWS EKS Auto Mode module implements AWS EKS Auto Mode clusters. The implementation leverages AWS's latest EKS features announced at re:Invent 2024, providing a more streamlined and managed Kubernetes experience.

## Overview

EKS Auto Mode implementation provides:

1. **Automated Cluster Management**
   - Fully managed Controlplane components
   - Built-in Karpenter integration for intelligent node provisioning
   - Automated add-on management (CNI, CoreDNS, kube-proxy)
   - Zero-touch controlplane and worker node lifecycle management

2. **Enhanced Security**
   - Supports API & Config based authentication
   - Pod-level security groups

3. **Simplified Operations**
   - Built-in upgrade management
   - Zero-config scaling
   - Automated node rotation

## Configuration

Configure EKS Auto Mode in your Pulumi stack:

```yaml
config:
  aws:
    eks:
      enabled: true
      clusters:
        - name: my-cluster
          mode: auto
          version: "1.31"
          node_groups:
            - name: default
              instance_types: [m6i.large]
              auto_mode_config:
                compute_enabled: true
                network_policy_enabled: true
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `mode` | Cluster mode (`auto` or `classic`) | `classic` |
| `version` | Kubernetes version | `1.31` |
| `node_groups[].instance_types` | EC2 instance types | `[m6i.large]` |
| `auto_mode_config.compute_enabled` | Enable compute management | `true` |
| `auto_mode_config.network_policy_enabled` | Enable network policies | `true` |

## Architecture

## Classic vs Auto Mode Comparison

### Classic EKS
- Manual node group management
- Self-managed add-ons
- Manual scaling configuration
- aws-auth ConfigMap management
- Manual node rotation
- Self-managed networking policies

### Auto Mode EKS
- Automated node provisioning
- AWS-managed add-ons
- Dynamic scaling with Karpenter
- API-based authentication
- Automated node rotation
- Built-in network policy support

## Implementation Details

## Cost Considerations

EKS Auto Mode includes additional costs:
- Per-node automation fee ($0.10 per node per hour)
- Managed add-on costs
- Standard EKS control plane costs

## Limitations

1. **Node Access**
   - No direct SSH access to nodes
   - Must use Kubernetes-native debugging
   - Limited customization of node configuration

2. **Add-ons**
   - Must use AWS-provided versions
   - Limited to supported add-on list
   - Version upgrades are automated

3. **Networking**
   - VPC CNI is required
   - Network policy implementation is fixed
   - Security group changes require pod restart

## Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html)
- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
