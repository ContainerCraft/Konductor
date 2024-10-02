# Konductor DevOps Template

## Introduction

Welcome to the Konductor DevOps Template.

This repository includes baseline dependencies and boilerplate artifacts for operating and developing cloud infrastructure automation.

Follow the steps below to configure AWS credentials, Kubernetes `kubectl` configuration, and verify access to AWS and EKS resources.

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

```bash {"id":"01J97M1349ZY70MQVHDB9BCR74"}
mkdir -p ~/.kube ~/.aws

```

### 2. Cloud Account Logins

Authenticate with your Pulumi account:

```bash {"id":"01J97M1349ZY70MQVHDE43DNY5"}
pulumi login

```

### 3. Load Environment Variables and AWS Credentials

Use Pulumi to load environment variables, configuration files, and credentials:

```bash {"id":"01J97M1349ZY70MQVHDGAFVNEB"}
export ENVIRONMENT="containercraft/NavtecaAwsCredentialsConfigSmce/navteca-aws-credentials-config-smce"
eval $(pulumi env open --format=shell $ENVIRONMENT)

```

Replace `<organization>`, `<project>`, and `<stack>` with your Pulumi organization, project name, and stack name.

### 4. Set Up AWS Configuration Files

Display the AWS configuration and credentials files:

```bash {"id":"01J97M1349ZY70MQVHDJSA5A4E"}
cat $GIT_CONFIG
cat $AWS_CONFIG_FILE
cat $AWS_SHARED_CREDENTIALS_FILE

```

Create symbolic links to these files in your home directory:

```bash {"id":"01J97M1349ZY70MQVHDJWF2SV7"}
ln -sf $GIT_CONFIG ~/.gitconfig
ln -sf $AWS_CONFIG_FILE ~/.aws/config
ln -sf $AWS_SHARED_CREDENTIALS_FILE ~/.aws/credentials

```

### 5. Install the SMCE CLI Tool

Clone the SMCE CLI repository:

```bash {"id":"01J97M1349ZY70MQVHDMSP1MHQ"}
git clone https://git.smce.nasa.gov/smce-administration/smce-cli.git ~/smce-cli

```

Create a symbolic link to the `smce` executable:

```bash {"id":"01J97M1349ZY70MQVHDQS03J8G"}
sudo ln -sf ~/smce-cli/smce /usr/local/bin/smce

```

Verify the installation:

```bash {"id":"01J97M1349ZY70MQVHDSWK0Q2Z"}
which smce

```

### 6. Configure AWS and Kubernetes Using SMCE CLI

Set up AWS Multi-Factor Authentication (MFA):

```bash {"id":"01J97M1349ZY70MQVHDT7NEEM1"}
smce awsconfig mfa

```

### 7. Test AWS CLI Access

Verify your AWS identity:

```bash {"id":"01J97M1349ZY70MQVHE11Y7TC6"}
aws sts get-caller-identity

```

List S3 buckets to confirm AWS access:

```bash {"id":"01J97M1349ZY70MQVHE452WAP0"}
aws s3 ls

```

Check the AWS CLI version:

```bash {"id":"01J97M1349ZY70MQVHE58JS7ND"}
aws --version

```

### 8. Update Kubernetes Configuration for EKS Cluster

Update your kubeconfig file to interact with your EKS cluster:

```bash {"id":"01J97M1349ZY70MQVHE78ZE70R"}
aws eks update-kubeconfig --profile main --region us-east-1 --name smce-gitops

```

Backup your existing Kubernetes configuration:

```bash {"id":"01J97M1349ZY70MQVHDX8JD5XZ"}
smce kubeconfig backup

```

Generate a new Kubernetes configuration:

```bash {"id":"01J97M1349ZY70MQVHDZVHZ3TQ"}
smce kubeconfig generate

```

Generate an authentication token for the EKS cluster:

```bash {"id":"01J97M1349ZY70MQVHE9A2GZGB"}
aws eks get-token --region us-east-1 --cluster-name smce-gitops --output json

```

Replace `<mfa-device-arn>` with your MFA device's ARN and provide your MFA token code in place of `$MFA_TOKEN`.

### 9. Configure Kubectl Alias and Verify Kubernetes Access

Create an alias for `kubectl` for convenience:

```bash {"id":"01J97M1349ZY70MQVHEAN1E8D0"}
alias k=kubectl

```

List available Kubernetes contexts:

```bash {"id":"01J97M1349ZY70MQVHEE3CJ1YZ"}
k config get-contexts

```

Retrieve the list of nodes in your Kubernetes cluster:

```bash {"id":"01J97M1349ZY70MQVHEGY0QEQW"}
k get nodes

```

Check the Kubernetes client and server versions with verbose output:

```bash {"id":"01J97M1349ZY70MQVHEHTZNV1Y"}
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

```bash {"id":"01J97M1349ZY70MQVHEJENFEAD"}
aws sts get-session-token \
  --duration-seconds 129600 \
  --profile default \
  --serial-number <mfa-device-arn> \
  --token-code $MFA_TOKEN
```
