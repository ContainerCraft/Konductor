# Konductor DevOps Template

## Introduction

This document provides step-by-step instructions to reproduce the setup for the Konductor DevOps Template. It includes configuring AWS credentials, setting up Kubernetes configurations, and verifying access to AWS and EKS resources.

## Prerequisites

Before you begin, ensure you have the following installed:

- **AWS CLI**: Version 2.x or higher.
- **Pulumi CLI**: For managing infrastructure as code.
- **Git**: For cloning repositories.
- **Kubectl**: For interacting with Kubernetes clusters.
- **sudo**: For executing administrative commands.

## Steps to Recreate

Follow the steps below to set up your environment:

### 1. Create the Kubernetes Configuration Directory

Create the `.kube` directory in your home directory if it doesn't exist:

```bash
mkdir -p ~/.kube
```

### 2. Cloud Account Logins

Authenticate with your Pulumi account:

```bash
pulumi login
```

### 3. Load Environment Variables and AWS Credentials

Use Pulumi to load environment variables, configuration files, and credentials:

```bash
export ENVIRONMENT="containercraft/NavtecaAwsCredentialsConfigSmce/navteca-aws-credentials-config-smce"
eval $(pulumi env open --format=shell $ENVIRONMENT)
```

Replace `<organization>`, `<project>`, and `<stack>` with your Pulumi organization, project name, and stack name.

### 4. Set Up AWS Configuration Files

Display the AWS configuration and credentials files:

```bash
cat $AWS_CONFIG_FILE
cat $AWS_SHARED_CREDENTIALS_FILE
```

Create symbolic links to these files in your home directory:

```bash
ln -s $AWS_CONFIG_FILE ~/.aws/config
ln -s $AWS_SHARED_CREDENTIALS_FILE ~/.aws/credentials
```

### 5. Install the SMCE CLI Tool

Clone the SMCE CLI repository:

```bash
git clone https://git.smce.nasa.gov/smce-administration/smce-cli.git ~/smce-cli
```

Create a symbolic link to the `smce` executable:

```bash
sudo ln -sf ~/smce-cli/smce /usr/local/bin/smce
```

Verify the installation:

```bash
which smce
```

### 6. Configure AWS and Kubernetes Using SMCE CLI

Set up AWS Multi-Factor Authentication (MFA):

```bash
smce awsconfig mfa
```

Backup your existing Kubernetes configuration:

```bash
smce kubeconfig backup
```

Generate a new Kubernetes configuration:

```bash
smce kubeconfig generate
```

### 7. Test AWS CLI Access

Verify your AWS identity:

```bash
aws sts get-caller-identity
```

List S3 buckets to confirm AWS access:

```bash
aws s3 ls
```

Check the AWS CLI version:

```bash
aws --version
```

### 8. Update Kubernetes Configuration for EKS Cluster

Update your kubeconfig file to interact with your EKS cluster:

```bash
aws eks update-kubeconfig --profile main --region us-east-1 --name smce-gitops
```

Generate an authentication token for the EKS cluster:

```bash
aws eks get-token --region us-east-1 --cluster-name smce-gitops --output json
```

Replace `<mfa-device-arn>` with your MFA device's ARN and provide your MFA token code in place of `$MFA_TOKEN`.

### 9. Configure Kubectl Alias and Verify Kubernetes Access

Create an alias for `kubectl` for convenience:

```bash
alias k=kubectl
```

List available Kubernetes contexts:

```bash
k config get-contexts
```

Retrieve the list of nodes in your Kubernetes cluster:

```bash
k get nodes
```

Check the Kubernetes client and server versions with verbose output:

```bash
k version -v=8
```

## Conclusion

By following these steps, you've set up your environment to interact with AWS services and your EKS cluster. This setup is essential for deploying and managing applications using the Konductor DevOps Template.

## Resources

- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [SMCE CLI Repository](https://git.smce.nasa.gov/smce-administration/smce-cli)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)

## Troubleshooting

**Note:** If you encounter authentication issues due to MFA requirements, test temporary session credentials using the following command:

```bash
aws sts get-session-token \
  --duration-seconds 129600 \
  --profile default \
  --serial-number <mfa-device-arn> \
  --token-code $MFA_TOKEN
```
