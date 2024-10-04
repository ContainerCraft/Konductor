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

### 1. Cloud Account Logins

Authenticate with your Pulumi account:

```bash {"id":"01J97M1349ZY70MQVHDE43DNY5","name":"login","tag":"setup"}
pulumi login

```

### 2. Load Environment Variables and AWS Credentials

Use Pulumi to load environment variables, configuration files, and credentials:

* NOTE: Replace `<organization>`, `<project>`, and `<stack>` with your Pulumi organization, project name, and stack name.

```bash {"id":"01J97M1349ZY70MQVHDGAFVNEB","name":"load-environments-and-secrets","tag":"setup"}
export ENVIRONMENT="containercraft/NavtecaAwsCredentialsConfigSmce/navteca-aws-credentials-config-smce"
eval $(pulumi env open --format=shell $ENVIRONMENT | tee ../.tmpenv; direnv allow)
ln -sf $GIT_CONFIG ~/.gitconfig
ln -sf $AWS_CONFIG_FILE ~/.aws/config
ln -sf $AWS_SHARED_CREDENTIALS_FILE ~/.aws/credentials
echo "Loaded environment $ENVIRONMENT"

```

### 3. Install the SMCE CLI Tool

Clone the SMCE CLI repository && Symlink `smce` cli:

```bash {"id":"01J97M1349ZY70MQVHDMSP1MHQ","name":"install-smce-cli","tag":"setup"}
mkdir -p ~/.local/bin; rm -rf ~/smce-cli
git clone https://git.smce.nasa.gov/smce-administration/smce-cli.git ~/smce-cli
ln -sf ~/smce-cli/smce ~/.local/bin/smce
smce --help; true

```

### 4. Configure AWS and Kubernetes Using SMCE CLI

Set up AWS Multi-Factor Authentication (MFA):

> TODO: enhance smce-cli to auto-export mfa env vars

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHDT7NEEM1","name":"smce-aws-mfa","tag":"aws"}
smce awsconfig mfa

```

### 7. Test AWS CLI Access

List S3 buckets to confirm AWS access && Verify your AWS identity:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHE452WAP0","name":"validate-aws-s3-ls","tag":"validate-aws"}
aws s3 ls
aws sts get-caller-identity

```

### 8. Update Kubernetes Configuration for EKS Cluster

Update your kubeconfig file to interact with your EKS cluster:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHE78ZE70R","name":"aws-get-ops-kubeconfig","tag":"kubeconfig"}
aws eks update-kubeconfig --profile main --region us-east-1 --name smce-gitops

```

Generate a new Kubernetes configuration:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHDZVHZ3TQ","name":"generate-smce-kubeconfig","tag":"kubeconfig"}
smce kubeconfig generate

```

Generate an authentication token for the EKS cluster:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHE9A2GZGB","name":"generate-eks-auth-token","tag":"kubeconfig"}
aws eks get-token --region us-east-1 --cluster-name smce-gitops --output json

```

Replace `<mfa-device-arn>` with your MFA device's ARN and provide your MFA token code in place of `$MFA_TOKEN`.

### 9. Configure Kubectl Alias and Verify Kubernetes Access

List available Kubernetes contexts:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHEE3CJ1YZ","name":"validate-kubeconfig-context-list","tag":"kubeconfig"}
kubectl --kubeconfig ~/.kube/smce config get-contexts

```

Retrieve the list of nodes in your Kubernetes cluster:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHEGY0QEQW","name":"validate-kube-get-nodes","tag":"kubeconfig"}
kubectl --kubeconfig ~/.kube/smce get nodes

```

Check the Kubernetes client and server versions with verbose output:

```bash {"excludeFromRunAll":"true","id":"01J97M1349ZY70MQVHEHTZNV1Y","name":"validate-kube-get-version","tag":"kubeconfig"}
kubectl version -v=8

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

```bash {"excludeFromRunAll":"true","id":"01J9CGCF9R0EWGHNN32BMZCGZY","name":"aws-sts-get-session-token","tag":"dbg"}
aws sts get-session-token \
  --duration-seconds 129600 \
  --profile default \
  --serial-number <mfa-device-arn> \
  --token-code $MFA_TOKEN
```
