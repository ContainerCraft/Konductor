# Zora Infrastructure Deployment Guide

## Introduction

This guide provides comprehensive instructions for deploying, managing, and cleaning up the Zora infrastructure using Pulumi and AWS. The infrastructure is designed as a multi-hybrid cloud platform with EKS clusters and supporting resources.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [S3 Backend Configuration](#s3-backend-configuration)
4. [Pulumi Configuration](#pulumi-configuration)
5. [Deployment](#deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Accessing the Cluster](#accessing-the-cluster)
8. [Cleanup and Troubleshooting](#cleanup-and-troubleshooting)

## Prerequisites

Before beginning deployment, ensure you have met all prerequisites via one of the methods below:

### via Devcontainer:

The included .devcontainer is  pre-configured with all dependencies and tools to develop and maintain the Zora IaC eliminating the need to install dependencies locally.

### via Local Dependencies:

- AWS CLI installed and configured with appropriate permissions
- Pulumi CLI installed (v3.0.0 or later)
- kubectl installed
- jq installed for JSON processing
- Proper AWS IAM permissions to create and manage:
  - S3 buckets
  - EKS clusters
  - VPCs and networking components
  - IAM roles and policies

## Initial Setup

First, configure your AWS credentials and ensure you have the necessary permissions:

```bash
aws configure
```

Verify your identity and permissions:

```bash
aws sts get-caller-identity
```

# Expand the s3 state backend instructions for first time setup instructions:

<details>
<summary>S3 Backend Configuration</summary>

Pulumi uses an S3 bucket to store state.

Create and configure the bucket before deploying for the first time, otherwise skip ahead to [Pulumi Configuration](#pulumi-configuration).

### Create the S3 Bucket

```bash
# Create the bucket in us-east-1
aws s3api create-bucket \
    --bucket konductor-smdc-admin-ucp-us-east-1 \
    --region us-east-1
```

### Enable Versioning

Versioning helps protect against accidental state loss:

```bash
# Enable versioning (recommended for state files)
aws s3api put-bucket-versioning \
    --bucket konductor-smdc-admin-ucp-us-east-1 \
    --versioning-configuration Status=Enabled
```

### Configure Encryption

Encrypt the bucket contents for security:

```bash
# Enable encryption (recommended for security)
aws s3api put-bucket-encryption \
    --bucket konductor-smdc-admin-ucp-us-east-1 \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'
```

### Block Public Access

Prevent public access to the bucket:

```bash
# Block public access (recommended for security)
aws s3api put-public-access-block \
    --bucket konductor-smdc-admin-ucp-us-east-1 \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

</details>

## Pulumi Configuration

### Set Pulumi Passphrase

The passphrase is used to encrypt sensitive information in the Pulumi state:

```bash
# TODO: Automate secret management with aws cli + Amazon Secrets Manager
# Option 1: Set passphrase via file (recommended for security)
echo 'SuperSecretMagicPassword9876!@#$' > ~/.pulumi/passphrase
export PULUMI_CONFIG_PASSPHRASE_FILE='~/.pulumi/passphrase'

# Option 2: Set passphrase directly (valid approach for ci runners)
export PULUMI_CONFIG_PASSPHRASE='SuperSecretMagicPassword9876!@#$'
```

### Login to Pulumi Backend

Connect Pulumi to the S3 backend:

```bash
# Bucket: konductor-smdc-admin-ucp-us-east-1
# Region: us-east-1
pulumi login 's3://konductor-smdc-admin-ucp-us-east-1?region=us-east-1&awssdk=v2'
```

### Initialize Pulumi Stack

Create and or configure the Pulumi stack:

```bash
# Export the stack name if not already set
export STACK_NAME="smdc-admin-ucp"
```

<details>
<summary>For first time deployment: Initialize Pulumi Stack</summary>

```bash
# Create a new stack
pulumi stack init $STACK_NAME
```

</details>

```bash
# Select the stack
pulumi stack select $STACK_NAME
```

```bash
# Configure AWS credentials (you'll be prompted for values)
pulumi config set --path --secret aws.access_key_id
pulumi config set --path --secret aws.secret_access_key

# Install dependencies
pulumi install

# Preview the deployment
pulumi preview
```

## Deployment

Deploy the infrastructure:

```bash
# Deploy with error handling and refresh
pulumi up --debug=false --continue-on-error=true --skip-preview=true --refresh=true
```

This command will:
- Create the VPC and networking components
- Deploy the EKS cluster
- Configure IAM roles and policies
- Set up necessary addons and components

The deployment may take 15-20 minutes to complete.

## Post-Deployment Configuration

After deployment, several manual steps are required:

### Configure GitLab Authentication

```bash
# Manual step: Install SSH public key secrets for GitLab authentication
# TODO: Automate this step with KMS + External Secrets + Amazon Secrets Manager

pulumi stack output ssh-flux-system --show-secrets
pulumi stack output ssh-flux-system-bootstrap --show-secrets

# Enroll the flux-system secret and flux-system-bootstrap secret into gitlab repos
# TODO: write `glab` cli commands for this
# TODO: write pulumi iac automation for this
```

### Configure Mattermost Secrets

```bash
# Manual step: Create Mattermost secrets
# TODO: Automate this step with KMS + External Secrets + Amazon Secrets Manager
manual: create smce-mattermost secret in flux-system namespace and monitoring namespace
```

### Download kubeconfig(s)

#### OIDC Kubeconfig

```bash
pulumi stack output kubeconfig_oidc --show-secrets | jq . | tee ~/.kube/config_oidc.json
```

#### Admin Kubeconfig

```bash
pulumi stack output kubeconfig_admin --show-secrets | jq . | tee ~/.kube/config_admin.json
```

### Verify Cluster Access

Verify you can access the cluster:

```bash
# Check pods
kubectl get pods

# Check Flux system secrets
kubectl -n flux-system get secrets flux-system-devops --output=jsonpath={.data.identity\\.pub} | base64 -d
kubectl get secrets -n flux-system
kubectl -n flux-system get secrets flux-system --output=jsonpath={.data.identity\\.pub} | base64 -d
```

### Update and Monitor

Run additional updates and monitor the cluster:

```bash
# Run another update
pulumi up --continue-on-error=true --skip-preview=true --debug=false --refresh=true

# Use k9s for cluster monitoring
k9s -A

# Check all pods
kubectl get pods -A -o wide
```

### Alternative Cluster Access

You can also access the cluster using the AWS CLI:

```bash
# Update kubeconfig using AWS CLI
aws eks update-kubeconfig --name smdc-ucp --region us-east-1 --alias smdc-ucp

# Check cluster information
aws eks list-clusters
aws eks describe-cluster --name smdc-ucp --query "cluster" --output json
aws eks describe-cluster --name smdc-ucp --query "cluster.version" --output json
```

### Crossplane Resources

If using Crossplane, you can check the resources:

```bash
# Check Crossplane VPC subnet resources
kubectl get composite xvpcsubnet.network.smce.io/smdc-aws-admin-vpc-subnets-kxvqc
kubectl describe xvpcsubnet.network.smce.io/smdc-aws-admin-vpc-subnets-kxvqc

# Check Crossplane EKS connection secrets
kubectl -n crossplane-system get secrets -o yaml smdc-aws-admin-eks-cluster-conn
kubectl -n crossplane-system get secrets smdc-aws-admin-eks-cluster-conn --output=jsonpath={.data.kubeconfig} | base64 -d | tee /tmp/kcfg
```

## Cleanup and Troubleshooting

When you need to destroy the infrastructure, follow these steps to ensure proper cleanup of all resources. The VPC cannot be deleted until all dependent resources are removed.

### 1. Destroy with Pulumi (Preferred Method)

The cleanest way to destroy all resources is using Pulumi:

```bash
# Select the stack
pulumi stack select $STACK_NAME

# Destroy all resources
pulumi destroy
```

### 2. Manual Cleanup (If Pulumi destroy is incomplete)

If Pulumi destroy fails with dependency violation errors (which is common), follow these steps to identify and remove the dependencies:

#### Step 1: Destroy deployed Kubernetes resources

```bash
nuke_namespace flux-system
```

#### Step 2: Identify VPC Resources Using the Discovery Tool

The repository includes a discovery tool that helps identify resources in a VPC:

```bash
# Use the aws-discover-vpc script to find all resources in the VPC
aws-discover-vpc eks-vpc-smdc-ucp
```

This will:
1. Automatically find the VPC ID based on the name pattern
2. List all resources in the VPC (subnets, network interfaces, security groups, etc.)
3. Identify dependencies for each subnet

#### Step 3: Remove VPC Endpoints

VPC endpoints often create network interfaces in subnets that block deletion:

```bash
# Find VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[*].[VpcEndpointId,ServiceName]" --output table

# Delete the VPC endpoints
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids vpce-XXXXXXXX
```

#### Step 4: Try Pulumi Destroy Again

After removing VPC endpoints, try Pulumi destroy again:

```bash
pulumi destroy
```

#### Step 5: Remove Security Groups

If the VPC still can't be deleted, you may need to remove security groups:

```bash
# List security groups in the VPC
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[*].[GroupId,GroupName]" --output table

# Delete non-default security groups (especially managed service groups)
aws ec2 delete-security-group --group-id sg-XXXXXXXX
```

#### Step 6: Final Pulumi Destroy

After removing all dependencies, run Pulumi destroy one more time:

```bash
pulumi destroy
```

### 3. Complete Manual Cleanup (If Needed)

If you need to perform a complete manual cleanup, follow these steps in order:

#### Step 1: Identify EKS Resources

```bash
# List EKS clusters
aws eks list-clusters

# Get details about the cluster
aws eks describe-cluster --name smdc-ucp
```

#### Step 2: Delete EKS Cluster Resources

Before deleting the cluster, remove all workloads:

```bash
# Set kubeconfig to access the cluster
aws eks update-kubeconfig --name smdc-ucp --region us-east-1

# Delete all namespaces except kube-system, default, and other AWS-managed ones
kubectl get ns -o name | grep -v "kube-system\|default\|kube-public\|kube-node-lease" | xargs kubectl delete

# Delete any load balancers (important to avoid orphaned resources)
kubectl get svc --all-namespaces -o json | jq -r '.items[] | select(.spec.type == "LoadBalancer") | .metadata.name + " " + .metadata.namespace' | while read name namespace; do kubectl delete svc $name -n $namespace; done
```

#### Step 3: Delete the EKS Cluster

```bash
# Delete the EKS cluster
aws eks delete-cluster --name smdc-ucp --region us-east-1

# Wait for the cluster to be fully deleted (this may take 10-15 minutes)
aws eks describe-cluster --name smdc-ucp --region us-east-1
# Keep checking until you get an error that the cluster doesn't exist
```

#### Step 4: Find and Delete EC2 Resources

Use the aws-discover-vpc script to identify all resources in the VPC:

```bash
# Find the VPC ID
aws-discover-vpc smdc-ucp
export VPC_ID="vpc-XXXXXXXX"  # Use the VPC ID from the output
```

Then delete resources in this order:

```bash
# Find and delete NAT Gateways
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query "NatGateways[*].NatGatewayId" --output text | xargs -I {} aws ec2 delete-nat-gateway --nat-gateway-id {}

# Wait for NAT Gateways to be deleted (this can take a few minutes)
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query "NatGateways[*].State" --output text

# Find and release Elastic IPs (that were used by NAT Gateways)
aws ec2 describe-addresses --query "Addresses[*].AllocationId" --output text | xargs -I {} aws ec2 release-address --allocation-id {}

# Find and delete any remaining EC2 instances
aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID" --query "Reservations[*].Instances[*].InstanceId" --output text | xargs -I {} aws ec2 terminate-instances --instance-ids {}

# Wait for instances to terminate
aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID" --query "Reservations[*].Instances[*].State.Name" --output text

# Find and delete VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[*].VpcEndpointId" --output text | xargs -I {} aws ec2 delete-vpc-endpoint --vpc-endpoint-id {}

# Find and delete security groups (except the default one)
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[?GroupName!='default'].GroupId" --output text | xargs -I {} aws ec2 delete-security-group --group-id {}

# Find and delete network interfaces
aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" --query "NetworkInterfaces[*].NetworkInterfaceId" --output text | xargs -I {} aws ec2 delete-network-interface --network-interface-id {}

# Find and delete route tables (except the main one)
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query "RouteTables[?Associations[?Main!=\`true\`]].RouteTableId" --output text | xargs -I {} aws ec2 delete-route-table --route-table-id {}

# Find and delete subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text | xargs -I {} aws ec2 delete-subnet --subnet-id {}

# Find and detach internet gateway
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query "InternetGateways[*].InternetGatewayId" --output text | xargs -I {} aws ec2 detach-internet-gateway --internet-gateway-id {} --vpc-id $VPC_ID

# Delete internet gateway
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query "InternetGateways[*].InternetGatewayId" --output text | xargs -I {} aws ec2 delete-internet-gateway --internet-gateway-id {}
```

#### Step 5: Delete the VPC

```bash
# Finally, delete the VPC
aws ec2 delete-vpc --vpc-id $VPC_ID
```

### 4. Cleanup S3 Bucket (Optional)

If you also want to delete the S3 bucket used for Pulumi state:

```bash
# Empty the bucket first (required before deletion)
aws s3 rm s3://konductor-smdc-admin-ucp-us-east-1 --recursive

# Delete the bucket
aws s3api delete-bucket --bucket konductor-smdc-admin-ucp-us-east-1 --region us-east-1
```

### 5. Common Dependency Issues and Solutions

Here are some common dependency issues you might encounter and how to resolve them:

#### VPC Endpoints

VPC endpoints create network interfaces in subnets that prevent deletion:

```bash
# Identify VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[*].[VpcEndpointId,ServiceName]" --output table

# Delete them
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids vpce-XXXXXXXX
```

#### Managed Service Security Groups

Services like GuardDuty create security groups that must be deleted manually:

```bash
# Look for security groups with names containing service names
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[*].[GroupId,GroupName]" --output table

# Delete them
aws ec2 delete-security-group --group-id sg-XXXXXXXX
```

#### Load Balancers

Load balancers create network interfaces and security groups:

```bash
# Find load balancers in the VPC
aws elbv2 describe-load-balancers --query "LoadBalancers[?VpcId=='$VPC_ID'].[LoadBalancerArn]" --output text | xargs -I {} aws elbv2 delete-load-balancer --load-balancer-arn {}
```

#### EKS Resources

EKS clusters create many resources that must be cleaned up:

```bash
# Delete all services with LoadBalancer type first
kubectl get svc --all-namespaces -o json | jq -r '.items[] | select(.spec.type == "LoadBalancer") | .metadata.name + " " + .metadata.namespace' | while read name namespace; do kubectl delete svc $name -n $namespace; done

# Then delete the cluster
aws eks delete-cluster --name smdc-ucp --region us-east-1
```

By following these steps in order, you should be able to successfully clean up all resources and avoid dependency violation errors.

## Conclusion

This guide has walked you through the process of deploying, managing, and cleaning up the Zora infrastructure. By following these steps, you can successfully deploy and manage your infrastructure using Pulumi and AWS.

For additional information or troubleshooting, refer to:
- [Pulumi AWS Documentation](https://www.pulumi.com/registry/packages/aws/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)


```bash
aws configure
vim ~/.aws/credentials
aws --profile smdc-admin sts get-caller-identity
aws eks update-kubeconfig --name smdc-ucp --region us-east-1 --alias smdc-ucp
aws eks list-clusters --query "clusters[*]" --output text | xargs -I {} aws eks describe-cluster --name {} --query "cluster.version" --output text
aws eks list-clusters
aws eks describe-cluster --name smdc-ucp --query "cluster" --output json
aws eks describe-cluster --name smdc-ucp --query "cluster.version" --output json
```

```bash
k get composite xvpcsubnet.network.smce.io/smdc-aws-admin-vpc-subnets-kxvqc
k describe xvpcsubnet.network.smce.io/smdc-aws-admin-vpc-subnets-kxvqc
k -n crossplane-system get secrets -o yaml smdc-aws-admin-eks-cluster-conn
k -n crossplane-system get secrets smdc-aws-admin-eks-cluster-conn --output=jsonpath={.data.kubeconfig}
k -n crossplane-system get secrets smdc-aws-admin-eks-cluster-conn --output=jsonpath={.data.kubeconfig} | b64 -d
k -n crossplane-system get secrets smdc-aws-admin-eks-cluster-conn --output=jsonpath={.data.kubeconfig} | base64 -d
k -n crossplane-system get secrets smdc-aws-admin-eks-cluster-conn --output=jsonpath={.data.kubeconfig} | base64 -d | tee /tmp/kcfg
```

## Cleanup and Troubleshooting

When you need to destroy the infrastructure, follow these steps to ensure proper cleanup of all resources. The VPC cannot be deleted until all dependent resources are removed.

### 1. Destroy with Pulumi (Preferred Method)

The cleanest way to destroy all resources is using Pulumi:

```bash
# Set your Pulumi passphrase if needed
export PULUMI_CONFIG_PASSPHRASE='SuperSecretMagicPassword9876!@#$'

# Select the stack
pulumi stack select smdc-admin-ucp

# Destroy all resources
pulumi destroy
```

### 2. Troubleshooting VPC Dependency Issues

If Pulumi destroy fails with dependency violation errors (which is common), follow these steps to identify and remove the dependencies:

#### Step 1: Identify VPC Resources Using the Discovery Tool

The repository includes a discovery tool that helps identify resources in a VPC:

```bash
# Use the aws-discover-vpc script to find all resources in the VPC
aws-discover-vpc smdc-ucp
```

This will:
1. Automatically find the VPC ID based on the name pattern
2. List all resources in the VPC (subnets, network interfaces, security groups, etc.)
3. Identify dependencies for each subnet

#### Step 2: Remove VPC Endpoints

VPC endpoints often create network interfaces in subnets that block deletion:

```bash
# Find VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[*].[VpcEndpointId,ServiceName]" --output table

# Delete the VPC endpoints
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids vpce-XXXXXXXX
```

#### Step 3: Try Pulumi Destroy Again

After removing VPC endpoints, try Pulumi destroy again:

```bash
pulumi destroy
```

#### Step 4: Remove Security Groups

If the VPC still can't be deleted, you may need to remove security groups:

```bash
# List security groups in the VPC
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[*].[GroupId,GroupName]" --output table

# Delete non-default security groups (especially managed service groups)
aws ec2 delete-security-group --group-id sg-XXXXXXXX
```

#### Step 5: Check for Other Dependencies

If the VPC still can't be deleted, check for these additional resources:

```bash
# Find and detach internet gateways
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query "InternetGateways[*].InternetGatewayId" --output text | xargs -I {} aws ec2 detach-internet-gateway --internet-gateway-id {} --vpc-id $VPC_ID
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query "InternetGateways[*].InternetGatewayId" --output text | xargs -I {} aws ec2 delete-internet-gateway --internet-gateway-id {}

# Find and delete NAT Gateways
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query "NatGateways[*].NatGatewayId" --output text | xargs -I {} aws ec2 delete-nat-gateway --nat-gateway-id {}

# Wait for NAT Gateways to be deleted (this can take a few minutes)
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query "NatGateways[*].State" --output text

# Find and delete network interfaces
aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" --query "NetworkInterfaces[*].NetworkInterfaceId" --output text | xargs -I {} aws ec2 delete-network-interface --network-interface-id {}

# Find and delete route tables (except the main one)
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query "RouteTables[?Associations[?Main!=\`true\`]].RouteTableId" --output text | xargs -I {} aws ec2 delete-route-table --route-table-id {}
```

#### Step 6: Final Pulumi Destroy

After removing all dependencies, run Pulumi destroy one more time:

```bash
pulumi destroy
```

### 3. Complete Manual Cleanup (If Needed)

If you need to perform a complete manual cleanup, follow these steps in order:

#### Step 1: Identify EKS Resources

```bash
# List EKS clusters
aws eks list-clusters

# Get details about the cluster
aws eks describe-cluster --name smdc-ucp
```

#### Step 2: Delete EKS Cluster Resources

Before deleting the cluster, remove all workloads:

```bash
# Set kubeconfig to access the cluster
aws eks update-kubeconfig --name smdc-ucp --region us-east-1

# Delete all namespaces except kube-system, default, and other AWS-managed ones
kubectl get ns -o name | grep -v "kube-system\|default\|kube-public\|kube-node-lease" | xargs kubectl delete

# Delete any load balancers (important to avoid orphaned resources)
kubectl get svc --all-namespaces -o json | jq -r '.items[] | select(.spec.type == "LoadBalancer") | .metadata.name + " " + .metadata.namespace' | while read name namespace; do kubectl delete svc $name -n $namespace; done
```

#### Step 3: Delete the EKS Cluster

```bash
# Delete the EKS cluster
aws eks delete-cluster --name smdc-ucp --region us-east-1

# Wait for the cluster to be fully deleted (this may take 10-15 minutes)
aws eks describe-cluster --name smdc-ucp --region us-east-1
# Keep checking until you get an error that the cluster doesn't exist
```

#### Step 4: Find and Delete EC2 Resources

Use the aws-discover-vpc script to identify all resources in the VPC:

```bash
# Find the VPC ID
aws-discover-vpc smdc-ucp
export VPC_ID="vpc-XXXXXXXX"  # Use the VPC ID from the output
```

Then delete resources in this order:

```bash
# Find and delete NAT Gateways
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query "NatGateways[*].NatGatewayId" --output text | xargs -I {} aws ec2 delete-nat-gateway --nat-gateway-id {}

# Wait for NAT Gateways to be deleted (this can take a few minutes)
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query "NatGateways[*].State" --output text

# Find and release Elastic IPs (that were used by NAT Gateways)
aws ec2 describe-addresses --query "Addresses[*].AllocationId" --output text | xargs -I {} aws ec2 release-address --allocation-id {}

# Find and delete any remaining EC2 instances
aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID" --query "Reservations[*].Instances[*].InstanceId" --output text | xargs -I {} aws ec2 terminate-instances --instance-ids {}

# Wait for instances to terminate
aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID" --query "Reservations[*].Instances[*].State.Name" --output text

# Find and delete VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[*].VpcEndpointId" --output text | xargs -I {} aws ec2 delete-vpc-endpoint --vpc-endpoint-id {}

# Find and delete security groups (except the default one)
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[?GroupName!='default'].GroupId" --output text | xargs -I {} aws ec2 delete-security-group --group-id {}

# Find and delete network interfaces
aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" --query "NetworkInterfaces[*].NetworkInterfaceId" --output text | xargs -I {} aws ec2 delete-network-interface --network-interface-id {}

# Find and delete route tables (except the main one)
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query "RouteTables[?Associations[?Main!=\`true\`]].RouteTableId" --output text | xargs -I {} aws ec2 delete-route-table --route-table-id {}

# Find and delete subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text | xargs -I {} aws ec2 delete-subnet --subnet-id {}

# Find and detach internet gateway
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query "InternetGateways[*].InternetGatewayId" --output text | xargs -I {} aws ec2 detach-internet-gateway --internet-gateway-id {} --vpc-id $VPC_ID

# Delete internet gateway
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query "InternetGateways[*].InternetGatewayId" --output text | xargs -I {} aws ec2 delete-internet-gateway --internet-gateway-id {}
```

#### Step 5: Delete the VPC

```bash
# Finally, delete the VPC
aws ec2 delete-vpc --vpc-id $VPC_ID
```

### 4. Cleanup S3 Bucket (Optional)

If you also want to delete the S3 bucket used for Pulumi state:

```bash
# Empty the bucket first (required before deletion)
aws s3 rm s3://konductor-smdc-admin-ucp-us-east-1 --recursive

# Delete the bucket
aws s3api delete-bucket --bucket konductor-smdc-admin-ucp-us-east-1 --region us-east-1
```

### 5. Common Dependency Issues and Solutions

Here are some common dependency issues you might encounter and how to resolve them:

#### VPC Endpoints

VPC endpoints create network interfaces in subnets that prevent deletion:

```bash
# Identify VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --query "VpcEndpoints[*].[VpcEndpointId,ServiceName]" --output table

# Delete them
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids vpce-XXXXXXXX
```

#### Managed Service Security Groups

Services like GuardDuty create security groups that must be deleted manually:

```bash
# Look for security groups with names containing service names
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[*].[GroupId,GroupName]" --output table

# Delete them
aws ec2 delete-security-group --group-id sg-XXXXXXXX
```

#### Load Balancers

Load balancers create network interfaces and security groups:

```bash
# Find load balancers in the VPC
aws elbv2 describe-load-balancers --query "LoadBalancers[?VpcId=='$VPC_ID'].[LoadBalancerArn]" --output text | xargs -I {} aws elbv2 delete-load-balancer --load-balancer-arn {}
```

#### EKS Resources

EKS clusters create many resources that must be cleaned up:

```bash
# Delete all services with LoadBalancer type first
kubectl get svc --all-namespaces -o json | jq -r '.items[] | select(.spec.type == "LoadBalancer") | .metadata.name + " " + .metadata.namespace' | while read name namespace; do kubectl delete svc $name -n $namespace; done

# Then delete the cluster
aws eks delete-cluster --name smdc-ucp --region us-east-1
```

By following these steps in order, you should be able to successfully clean up all resources and avoid dependency violation errors.
