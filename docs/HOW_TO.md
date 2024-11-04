# Konductor DevOps Template

## Introduction

Welcome to the Konductor DevOps Template.

This repository includes baseline dependencies and boilerplate artifacts for operating and developing cloud infrastructure automation.

Follow the steps below to configure AWS credentials, set up your development environment, and verify access to AWS and EKS resources.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.8 or higher.
- **Poetry**: For dependency management and packaging. [Install Poetry](https://python-poetry.org/docs/#installation).
- **AWS CLI**: Version 2.x or higher.
- **Pulumi CLI**: For managing infrastructure as code.
- **Git**: For cloning repositories.
- **Kubectl**: For interacting with Kubernetes clusters.
- **sudo**: For executing administrative commands.

> **Note:** All dependencies are automatically supplied in the [ghcr.io/containercraft/devcontainer](https://github.com/containercraft/devcontainer) image powering the VSCode Dev Container included in this repository by the [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) and [.devcontainer/Dockerfile](.devcontainer/Dockerfile).

## Steps to Recreate

Follow the steps below to set up your environment:

### 1. Initialize the Development Environment

#### a. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/containercraft/konductor.git
cd konductor
```

#### b. Install Dependencies with Poetry

We use [Poetry](https://python-poetry.org/) for dependency management and packaging. Poetry ensures that our development environment is consistent, dependencies are properly managed, and collaboration is streamlined.

Install the project dependencies:

```bash
poetry install
```

This command will create a virtual environment and install all dependencies specified in `pyproject.toml`.

#### c. Activate the Virtual Environment

Activate the virtual environment:

```bash
poetry shell
```

Alternatively, you can prefix commands with `poetry run`.

#### d. Configure Pulumi to Use Poetry

Ensure that `Pulumi.yaml` specifies Poetry as the toolchain:

```yaml
name: your-pulumi-project
runtime:
  name: python
  options:
    toolchain: poetry
```

#### e. Install Pulumi Dependencies

Install Pulumi dependencies:

```bash
pulumi install
```

This command ensures that Pulumi recognizes and utilizes the Poetry-managed environment.

### 2. Enforce Type Checking with Pyright

Type checking enhances code reliability and maintainability. We enforce strict type checking using [Pyright](https://github.com/microsoft/pyright).

#### a. Verify Type Checking

Run Pyright to check for type errors:

```bash
poetry run pyright
```

Ensure that there are no type errors before proceeding. If type errors are detected, fix them according to the standards outlined in [PULUMI_PYTHON.md](../docs/PULUMI_PYTHON.md).

### 3. Authenticate with Pulumi

Login to Pulumi Cloud:

```bash
pulumi login
```

### 4. Load Environment Variables and AWS Credentials

Use Pulumi to load environment variables, configuration files, and credentials.

*Note:* Replace `<organization>`, `<project>`, and `<stack>` with your Pulumi organization, project name, and stack name.

```bash
export ENVIRONMENT="<organization>/<project>/<stack>"
eval $(pulumi env open --format=shell $ENVIRONMENT | tee .tmpenv; direnv allow)
echo "Loaded environment $ENVIRONMENT"

alias aws='aws --profile smdc-cba'
```

### 5. Validate AWS CLI Access

Get Caller Identity to verify your AWS identity:

```bash
aws --profile smdc-cba sts get-caller-identity
```

### 6. Deploy Infrastructure as Code (IaC)

Before deploying, ensure that your code passes type checking to maintain code quality.

#### a. Run Type Checking

```bash
poetry run pyright
```

If type errors are detected, the deployment will halt, and errors will be displayed.

#### b. Deploy with Pulumi

Deploy the infrastructure using Pulumi:

```bash
pulumi up --yes --stack <organization>/<project>/<stack> --skip-preview --refresh
```

Replace `<organization>/<project>/<stack>` with your specific Pulumi stack information.

### 7. Install the SMCE CLI Tool

Clone the SMCE CLI repository and set up the `smce` CLI:

```bash
cd ~
rm -rf ~/smce-cli ~/.local/bin/smce
ln -sf $GIT_CONFIG ~/.gitconfig

git clone https://git.smce.nasa.gov/smce-administration/smce-cli.git ~/smce-cli
cd ~/smce-cli

mkdir -p ~/.local/bin
cp -f ~/smce-cli/smce ~/.local/bin/smce
chmod +x ~/.local/bin/smce

smce --help || true
```

### 8. Configure AWS and Kubernetes Using SMCE CLI

Set up AWS Multi-Factor Authentication (MFA):

> **Note:** Enhance `smce-cli` to auto-export MFA environment variables.

```bash
smce awsconfig mfa
```

### 9. Test AWS CLI Access

List S3 buckets to confirm AWS access and verify your AWS identity:

```bash
aws s3 ls
aws sts get-caller-identity
```

### 10. Update Kubernetes Configuration for EKS Cluster

Update your kubeconfig file to interact with your EKS cluster:

```bash
aws eks update-kubeconfig --profile main --region us-east-1 --name smce-gitops
```

Generate a new Kubernetes configuration:

```bash
smce kubeconfig generate
```

Generate an authentication token for the EKS cluster:

```bash
aws eks get-token --region us-east-1 --cluster-name smce-gitops --output json
```

Replace `<mfa-device-arn>` with your MFA device's ARN and provide your MFA token code in place of `$MFA_TOKEN`.

### 11. Configure Kubectl Alias and Verify Kubernetes Access

List available Kubernetes contexts:

```bash
kubectl --kubeconfig ~/.kube/smce config get-contexts
```

Retrieve the list of nodes in your Kubernetes cluster:

```bash
kubectl --kubeconfig ~/.kube/smce get nodes
```

Check the Kubernetes client and server versions with verbose output:

```bash
kubectl version -v=8
```

## Conclusion

By following these steps, you've set up your environment to interact with AWS services and your EKS cluster. This setup is essential for deploying and managing applications using the Konductor DevOps Template.

## Resources

- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [SMCE CLI Repository](https://git.smce.nasa.gov/smce-administration/smce-cli)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pyright Documentation](https://github.com/microsoft/pyright)

## Troubleshooting

**Note:** If you encounter authentication issues due to MFA requirements, test temporary session credentials using the following command:

```bash
aws sts get-session-token \
  --duration-seconds 129600 \
  --profile default \
  --serial-number <mfa-device-arn> \
  --token-code $MFA_TOKEN
```

## Bonus: Launch Kubernetes in Docker

```bash
cd ..
task kubernetes
```
