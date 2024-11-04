# Getting Started with Konductor

Welcome to Konductor! This guide will help you quickly set up and begin using the Konductor Infrastructure as Code (IaC) platform. Whether you're new to DevOps or an experienced platform engineer, this guide provides everything you need to get started.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup](#quick-setup)
3. [Initial Configuration](#initial-configuration)
4. [First Deployment](#first-deployment)
5. [Next Steps](#next-steps)
6. [Troubleshooting](#troubleshooting)
7. [Getting Help](#getting-help)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.8 or higher
- **Poetry**: For dependency management ([Install Poetry](https://python-poetry.org/docs/#installation))
- **Pulumi CLI**: For infrastructure management ([Install Pulumi](https://www.pulumi.com/docs/get-started/install/))
- **Git**: For version control
- **AWS CLI** (optional): If working with AWS resources
- **kubectl** (optional): If working with Kubernetes resources

> **Note**: All dependencies are automatically supplied if you use the provided Dev Container with VS Code.

## Quick Setup

### 1. Create Your Project

Choose one of these methods to create your project:

#### Option A: Use GitHub Template (Recommended)

1. Visit the [Konductor Template Repository](https://github.com/containercraft/konductor).
2. Click "Use this template."
3. Fill in your repository details.
4. Clone your new repository:
   ```bash
   git clone https://github.com/your-username/your-project-name.git
   cd your-project-name
   ```

#### Option B: Clone Directly

```bash
git clone https://github.com/containercraft/konductor.git
cd konductor
```

### 2. Set Up Development Environment

#### Using Dev Container (Recommended)

1. Install [VS Code](https://code.visualstudio.com/) and the [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
2. Open the project in VS Code.
3. When prompted, click "Reopen in Container."

#### Manual Setup

1. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

2. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Initial Configuration

### 1. Configure Pulumi

1. Log in to Pulumi:
   ```bash
   pulumi login
   ```

2. Create a new stack:
   ```bash
   pulumi stack init dev
   ```

3. Configure your cloud provider (example for AWS):
   ```bash
   pulumi config set aws:region us-west-2
   ```

### 2. Set Up Cloud Provider Credentials

#### For AWS:

```bash
aws configure
```

Follow the prompts to enter your AWS credentials.

> **Security Note**: Always follow your organization's security policies when handling credentials.

## First Deployment

1. **Preview Changes**:
   ```bash
   pulumi preview
   ```

2. **Deploy Infrastructure**:
   ```bash
   pulumi up
   ```

3. **Verify Deployment**:
   ```bash
   pulumi stack output
   ```

## Next Steps

After completing your initial setup, explore these resources:

1. **[User Guide](./user_guide/README.md)**
   - Learn about Konductor's features and capabilities.
   - Understand best practices for using the platform.

2. **[Module Documentation](./modules/README.md)**
   - Explore available modules.
   - Learn how to use specific modules like AWS or cert-manager.

3. **[Developer Guide](./developer_guide/README.md)**
   - Contribute to Konductor.
   - Create custom modules.

## Troubleshooting

Common issues and their solutions:

### Poetry Installation Issues

**Problem**: Poetry installation fails.
**Solution**: Try installing with pip:

   ```bash
   pip install --user poetry
   ```

### Pulumi Login Issues

**Problem**: Cannot log in to Pulumi.
**Solution**: Ensure you have created an account at [app.pulumi.com](https://app.pulumi.com) and create a new Personal Access Token (PAT).

For more troubleshooting help, see our [FAQ and Troubleshooting Guide](./user_guide/faq_and_troubleshooting.md).

## Getting Help

- **Documentation**: Browse our [comprehensive documentation](./README.md).
- **Community**: Join our [Discord community](https://discord.gg/Jb5jgDCksX).
- **Issues**: Report problems on our [GitHub Issues](https://github.com/containercraft/konductor/issues).
- **Discussions**: Start a discussion in our [GitHub Discussions](https://github.com/containercraft/konductor/discussions).

---

**Next**: Explore the [User Guide](./user_guide/README.md) to learn more about using Konductor effectively.
