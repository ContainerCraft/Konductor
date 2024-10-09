# Konductor DevOps Template Repository

## Overview

This repository serves as a comprehensive template for starting new DevOps projects from scratch. It is designed to be cloned as a GitHub template repository, providing a fully-configured environment for deploying and managing cloud-native infrastructure using VSCode with Kubernetes and Pulumi boilerplate as a starting line.

Whether you're building for on-premises, cloud, or local environments, this template streamlines the setup and deployment processes, enabling you to focus on building and innovating.

Join the community in the [ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX) to discuss, collaborate, and contribute!

## Features

- **AWS LandingZone**: Automated Kubernetes cluster setup using Talos.
- **Kubernetes Deployment**: Automated Kubernetes cluster setup using Talos.
- **Pulumi IaC Integration**: Infrastructure as Code management with Pulumi.
- **Runme Integration**: Execute documented tasks directly from the README.md.
- **GitHub Actions Support**: CI/CD pipelines configured for automated testing and deployment.

## Using This Template to Start a New Project

This repository is designed as a template, allowing you to quickly bootstrap new DevOps projects with a fully-configured environment. Follow the steps below to create a new project from this template.

### Step 1: Create a New Repository from the Template

1. **Navigate to the Template Repository:**

   Visit the [Konductor DevOps Template Repository](https://github.com/ContainerCraft/Konductor) on GitHub.

2. **Use the "Use this template" Button:**

   - Click the green `Use this template` button located at the top-right of the repository page.
   - In the form that appears, provide a name for your new repository and decide if it should be public or private.
   - Click `Create repository from template` to generate your new repository.

### Step 2: Clone Your New Repository

1. **Clone the Repository to Your Local Machine:**

   Once your new repository is created, clone it to your local machine using Git.

   ```bash
   git clone https://github.com/YourUsername/YourNewRepoName.git
   cd YourNewRepoName
   ```

2. **Initialize the Development Environment:**

   If you're using [GitHub Codespaces](https://github.com/features/codespaces) or a local development environment with Docker, you can launch directly into the pre-configured environment.

   - **GitHub Codespaces:** Click the `Code` button and select `Open with Codespaces`, or follow the instructions in the Quickstart section of this README.
   - **Local Development:** Follow the instructions in the `Getting Started` section to set up your local environment.

### Step 3: Customize the Configuration

1. **Update Configuration Files:**

   - Customize the `.env` file with your project-specific environment variables.
   - Modify the `Taskfile.yaml` to include tasks specific to your project.
   - Adjust the Pulumi configuration files under `.pulumi` to match your cloud and infrastructure setup.

2. **Set Up Your Pulumi Stack:**

   Configure your Pulumi stack settings to match your project environment by following the steps in the `Getting Started` section.

### Step 4: Start Developing

1. **Deploy the Infrastructure:**

   Use the pre-configured tasks to deploy your infrastructure, as detailed in the Quickstart section.

   ```bash
   task kubernetes
   task deploy
   ```

2. **Build and Iterate:**

   With your infrastructure deployed, you can now focus on developing your application, iterating on your DevOps processes, and refining your setup.

### Step 5: Push Your Changes

1. **Commit and Push:**

   After making changes, commit them to your repository.

   ```bash
   git add .
   git commit -m "Initial setup and configuration"
   git push origin main
   ```

2. **Collaborate and Contribute:**

   Share your repository with your team, collaborate on features, and contribute back to the original template if you make improvements that could benefit others.

### Tips for Success

- **Keep your dependencies up to date:** Regularly update the tools and libraries used in your project.
- **Document your changes:** Update the README and other documentation as your project evolves.
- **Engage with the community:** Join the [ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX) to get support and share your experiences.

## How-To (Boilerplate Instructions)

This repository is designed to be used as a template for new DevOps projects. Follow the steps below to clone and configure your environment.

### Prerequisites

Ensure you have the following tools and accounts:

1. [GitHub](https://github.com)
2. [Pulumi Cloud](https://app.pulumi.com/signup)
3. [Microsoft Edge](https://www.microsoft.com/en-us/edge) or [Google Chrome](https://www.google.com/chrome)

### Quickstart

Follow these steps to get your environment up and running:

1. **Clone the Repository:**

   Clone this repository to your GitHub account using the "Use this template" button.

2. **Launch in GitHub Codespaces:**

   Start a new GitHub Codespace with the following options:

   - **Branch:** `main`
   - **Dev Container Configuration:** `konductor`
   - **Region:** Your choice
   - **Machine Type:** 4 cores, 16 GB RAM, or better

3. **Open the Integrated Terminal:**

   Use `` Ctrl + ` `` to open the VSCode integrated terminal.

4. **Authenticate Credentials:**

   Login to Pulumi Cloud and other required services.

   ```bash {"id":"01J5VC1KTJBR22WEDNSSGTNAX4","name":"login"}
   task login
   ```

5. **Configure the Pulumi Stack:**

   Set up Pulumi stack parameters.

   ```bash {"id":"01J5VC1KTJBR22WEDNSWYBKNQS","name":"configure"}
   export ORGANIZATION="${GITHUB_USER:-${GITHUB_REPOSITORY_OWNER:-}}"
   export DEPLOYMENT="${RepositoryName:-}"
   task configure
   ```

6. **Deploy Kubernetes:**

   Deploy Kubernetes using Talos.

   ```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNSX4RHEG2","name":"kubernetes"}
   task kubernetes
   ```

7. **Deploy the Platform:**

   Deploy the KubeVirt PaaS infrastructure.

   ```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNSZW7QADA","name":"deploy"}
   task deploy
   ```

10. **Cleanup:**

    Clean up all Kubernetes and Pulumi resources when you're done.

    ```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT7BDRMAV","name":"clean"}
    task clean-all
    ```

## Contributing

Contributions are welcome! This template is intended to evolve with the needs of the community. Learn how to contribute by reading our [CONTRIBUTING.md](https://github.com/ContainerCraft/Konductor/issues/22).

### Developing and Testing

Use the `act` tool to test GitHub Actions locally before pushing your changes.

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT92WYZEH"}
task act
```

## Community and Support

Join our community to discuss, learn, and contribute:

- **[ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX)**
- **[Konductor Project FAQ](FAQ.md)**
