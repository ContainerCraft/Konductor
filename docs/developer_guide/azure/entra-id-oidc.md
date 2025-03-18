# Azure Entra ID OIDC Authentication with Amazon EKS

This guide details the configuration of Azure Entra ID (formerly Azure AD) as an OpenID Connect (OIDC) identity provider for Amazon EKS clusters. This enables `kubectl` authentication against Amazon AWS EKS Kubernetes clusters via Azure Entra ID, leveraging Kubernetes RBAC for authorization.

## Table of Contents

1. [About This Guide](#1-about-this-guide)
2. [Prerequisites](#2-prerequisites)
3. [Azure Portal Configuration](#3-azure-portal-configuration)
4. [EKS OIDC Configuration](#4-eks-oidc-configuration)
5. [Kubernetes RBAC Setup](#5-kubernetes-rbac-setup)
6. [Client Configuration](#6-client-configuration)
7. [Testing and Validation](#7-testing-and-validation)
8. [Troubleshooting Guide](#8-troubleshooting-guide)
9. [Reference: Kubeconfig Structure](#9-reference-kubeconfig-structure)

## 1. About This Guide

Implementation provides:

- **Seamless authentication** via Entra ID instead of AWS IAM users.
- **RBAC enforcement** for precise access control to EKS clusters.
- **Reduced reliance on static IAM credentials** in Kubernetes environments.
- **Improved auditability and centralized user management** using Azure AD logs.

## 2. Prerequisites
Before configuring Entra ID OIDC authentication with EKS, ensure that the following requirements are met:

### 2.1 Administrative Permissions
- **Azure Entra ID Administrator:** Requires permissions to manage **App Registrations, Groups, and API Permissions**.
- **AWS IAM Administrator:** Requires permissions to manage EKS clusters and configure OIDC identity providers.
- **Kubernetes Cluster Admin:** Requires permissions to create **ClusterRoleBindings** and manage `kubectl` configurations.

### 2.2 Required CLI Tools
Ensure the following tools are installed and updated on your system:
```bash
# kubectl
# on MacOS
brew install kubernetes-cli
# on Windows
choco install kubernetes-cli

# kubelogin
# https://azure.github.io/kubelogin
# on MacOS
brew install Azure/kubelogin/kubelogin

# on Windows
az aks install-cli

# on Linux
curl -LO "https://github.com/Azure/kubelogin/releases/download/v0.0.30/kubelogin-linux-amd64"
chmod +x kubelogin-linux-amd64
sudo mv kubelogin-linux-amd64 /usr/local/bin/kubelogin
```


### 2.3 Required Configurations & Secrets
The following **values and configurations** must be collected or created before beginning implementation:

#### **Azure Entra ID Values:**
- **Application (client) ID**: Obtained from **App Registrations** in Azure.
- **Directory (tenant) ID**: Found in **Azure Active Directory Overview**.
- **Group Object IDs**: Retrieve from **Azure AD → Groups** for mapping to Kubernetes RBAC.

#### **AWS and EKS Configuration:**
- **Amazon EKS Cluster Name**: Used to configure `kubectl` access.
- **OIDC Issuer URL**: Found in **AWS Console → EKS → Cluster Configuration**.
  ```bash
  aws eks list-clusters --profile smdc-admin
  ```
- **EKS API Server Endpoint**: Retrieve via AWS CLI:
  ```bash
  aws eks describe-cluster --name <cluster-name> --query "cluster.endpoint" --output text
  ```
- **Certificate Authority Data**: Retrieve using AWS CLI:
  ```bash
  aws eks describe-cluster --name <cluster-name> --query "cluster.certificateAuthority.data" --output text
  ```

---

## 3. Azure Portal Configuration

### 3.1 Create App Registration
1. Login to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Configure the application:
   ```yaml
   Name: eks-auth-smdc-ucp  # Replace with real cluster / app name
   Supported account types: Accounts in this organizational directory only
   Redirect URI: (leave blank)
   ```
5. Click **Register**
6. Record these values:
   - **Application (client) ID**
   - **Directory (tenant) ID**

### 3.2 Configure Authentication
1. Open new app registration:
2. Select **Authentication** from the left menu
3. Under **Advanced settings**:
   - Set **Allow public client flows** to **Yes**
   - Click **Save**

### 3.3 Configure Token
1. Select **Token configuration**
2. Click **Add groups claim**
3. Configure:
   ```yaml
   Token type: ID
   Group types: Security groups
   Emit groups as: Group ID
   ```
4. Click **Add**

### 3.4 Create Azure Groups
1. Navigate to **Azure Active Directory** → **Groups**
2. Click **New group**
3. Create admin group:
   ```yaml
   Group type: Security
   Group name: eks-admins
   Group description: EKS Cluster Administrators
   ```
4. Create developer group:
   ```yaml
   Group type: Security
   Group name: eks-developers
   Group description: EKS Cluster Developers
   ```
5. Record the **Object ID** for each group

### 3.5 Add Users to Groups
1. Select newly created group
2. Click **Members** → **Add members**
3. Search and select users
4. Click **Select** to add them

## 4. EKS OIDC Configuration

### 4.1 Update EKS Configuration
For Pulumi stack configuration:

```yaml
config:
  zora:aws:
    eks:
      clusters:
        - name: smdc-ucp
          oidc:
            enabled: true
            client_id: "<client-id>"
            issuer_url: "https://sts.windows.net/<tenant-id>/"  # Note: Changed from login.microsoftonline.com
            groups_claim: "groups"
            groups_prefix: "azure:"
            username_claim: "sub"  # Changed from "upn"
            username_prefix: "azure:"
            required_claims:
              aud: "<client-id>"
```

### 4.2 Apply Configuration
```bash
# Deploy changes with Pulumi
pulumi up
```

### 4.3 Verify OIDC Provider Configuration
Ensure the OIDC provider is properly set up in AWS:
```bash
aws eks describe-cluster --name <eks-cluster-name> --query "cluster.identity.oidc.issuer" --output text
```

If the output is a valid OIDC issuer URL, the configuration is successful.

### 4.4 Important Configuration Notes

1. **Username Claim**: 
   - Use `sub` instead of `upn` for the username_claim
   - The `sub` claim is more reliable and stable than `upn`

2. **Issuer URL**: 
   - Use `https://sts.windows.net/<tenant-id>/` format
   - Do not use the login.microsoftonline.com URL

3. **Cluster Name in Kubeconfig**:
   - Use the full ARN format: `arn:aws:eks:region:account:cluster/name`
   - This ensures proper identification of the cluster

4. **Context Name**:
   - Use the format: `cluster/<cluster-name>`
   - This matches AWS EKS conventions

## 5. Kubernetes RBAC Setup

### 5.1 Create Admin Role Binding
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: azure-admin-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: Group
  name: "azure:<admin-group-object-id>"  # Replace with your eks-admins group Object ID
  apiGroup: rbac.authorization.k8s.io
```

### 5.2 Create Developer Role Binding
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: azure-developer-binding
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: edit
subjects:
- kind: Group
  name: "azure:<developer-group-object-id>"  # Replace with your eks-developers group Object ID
  apiGroup: rbac.authorization.k8s.io
```

## 6. Client Configuration

### 6.1 Create Kubeconfig
Create a new kubeconfig file:

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: <your-cluster-ca-data>
    server: https://<your-cluster-endpoint>.gr7.us-east-1.eks.amazonaws.com
  name: arn:aws:eks:us-east-1:<account-id>:cluster/<cluster-name>
contexts:
- context:
    cluster: arn:aws:eks:us-east-1:<account-id>:cluster/<cluster-name>
    user: kubelogin
  name: cluster/<cluster-name>
current-context: cluster/<cluster-name>
kind: Config
preferences: {}
users:
- name: kubelogin
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      args:
      - get-token
      - --server-id
      - <client-id>
      - --client-id
      - <client-id>
      - --tenant-id
      - <tenant-id>
      command: kubelogin
      env: null
      interactiveMode: IfAvailable
      provideClusterInfo: false
```

## 7. Testing and Validation

### 7.1 Test Authentication
```bash
# Set KUBECONFIG
export KUBECONFIG=~/.kube/config-azure

# Test access
kubectl get pods
```

You should be prompted to authenticate via browser or device code.

### 7.2 Verify Group Membership
```bash
# List your current permissions
kubectl auth can-i --list
```

## 8. Troubleshooting Guide

### 8.1 Common Issues and Solutions

1. **Authentication Failures**
   ```bash
   # Test token acquisition directly
   kubelogin get-token \
     --server-id <client-id> \
     --client-id <client-id> \
     --tenant-id <tenant-id>
   ```

2. **Group Membership Issues**
   - Verify group claims in token:
   ```bash
   # Get token and decode with jwt.io
   kubelogin get-token --server-id <client-id> --client-id <client-id> --tenant-id <tenant-id>
   # Look for "groups" claim in decoded token
   ```

3. **RBAC Binding Issues**
   ```bash
   # Verify binding exists
   kubectl get clusterrolebinding azure-admin-binding -oyaml
   
   # Verify group name format
   # Should be: azure:<group-object-id>
   ```

4. **Kubeconfig Validation**
   ```bash
   # Test with verbose logging
   kubectl --kubeconfig=/path/to/config get pods -v=6
   
   # Verify cluster connectivity
   kubectl --kubeconfig=/path/to/config cluster-info
   ```

### 8.2 Common Error Messages

1. "Error loading config file"
   - Check YAML syntax
   - Verify file permissions
   - Ensure no special characters in the file

2. "Unable to load root certificates"
   - Verify certificate-authority-data is correct
   - Check cluster endpoint URL
   - Ensure AWS credentials are valid

3. "Authentication failed"
   - Verify Application ID and Tenant ID
   - Check Azure group membership
   - Validate RBAC bindings exist

## 9. Reference: Kubeconfig Structure

### 9.1 Key Components
```yaml
apiVersion: v1
kind: Config
current-context: "<context-name>"  # Active context

clusters:  # Define cluster endpoints
- name: "<cluster-name>"
  cluster:
    server: "https://<eks-endpoint>"
    certificate-authority-data: "<base64-encoded-ca>"

contexts:  # Link clusters and users
- name: "<context-name>"
  context:
    cluster: "<cluster-name>"
    user: "<user-name>"

users:  # Define authentication methods
- name: "<user-name>"
  user:
    exec:  # Azure authentication configuration
      command: kubelogin
      args:
      - get-token
      - --server-id
      - "<client-id>"
      - --client-id
      - "<client-id>"
      - --tenant-id
      - "<tenant-id>"
```

### 9.2 Important Fields Explained

1. **clusters**
   - `server`: EKS API endpoint
   - `certificate-authority-data`: Cluster CA certificate

2. **contexts**
   - Links a cluster with a user
   - Defines namespace (optional)

3. **users**
   - `exec`: Uses external authentication
   - `command`: Specifies kubelogin
   - `args`: Azure-specific configuration
     - `server-id`: App Registration client ID
     - `tenant-id`: Azure Directory ID

### 9.3 Environment Variables
```bash
KUBECONFIG=~/.kube/config-oidc   # Specify config file
AZURE_TENANT_ID=<tenant-id>      # Override tenant ID
AZURE_CLIENT_ID=<client-id>      # Override client ID
```

## Additional Resources
- [Azure Entra ID Documentation](https://learn.microsoft.com/en-us/entra/identity/)
- [EKS OIDC Documentation](https://docs.aws.amazon.com/eks/latest/userguide/authenticate-oidc-identity-provider.html)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [kubelogin GitHub](https://github.com/Azure/kubelogin)