# Konductor DevOps Template Repository

## Overview

This repository serves as a comprehensive template for starting new DevOps projects from scratch. It is designed to be cloned as a GitHub template repository, providing a fully-configured environment for deploying and managing cloud-native infrastructure using VSCode with Kubernetes and Pulumi boilerplate as a starting point.

Whether you're building for on-premises, cloud, or local environments, this template streamlines the setup and deployment processes, enabling you to focus on building and innovating.

Join the community in the [ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX) to discuss, collaborate, and contribute!

## Features

- **AWS LandingZone**: Automated Kubernetes cluster setup using Talos.
- **Kubernetes Deployment**: Automated Kubernetes cluster setup using Talos.
- **Pulumi IaC Integration**: Infrastructure as Code management with Pulumi, using Python and best practices.
- **Runme Integration**: Execute documented tasks directly from the README.md.
- **GitHub Actions Support**: CI/CD pipelines configured for automated testing and deployment.
- **Dependency Management with Poetry**: Manage Python dependencies and environments using Poetry.
- **Strict Type Checking with Pyright**: Enforce code quality through strict type checking.

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

   We use [Poetry](https://python-poetry.org/) for dependency management and packaging. Poetry ensures that our development environment is consistent, dependencies are properly managed, and collaboration is streamlined.

   **Install Poetry:**

   Ensure that `poetry` is added to your system's PATH. Refer to the [official installation guide](https://python-poetry.org/docs/#installation) for detailed instructions.

   **Install Dependencies and Create Virtual Environment:**

   ```bash
   poetry install
   ```

   **Activate the Virtual Environment:**

   ```bash
   poetry shell
   ```

   Alternatively, you can prefix commands with `poetry run`.

3. **Configure Pulumi to Use Poetry:**

   Ensure that `Pulumi.yaml` specifies Poetry as the toolchain:

   ```yaml
   name: your-pulumi-project
   runtime:
     name: python
     options:
       toolchain: poetry
   ```

4. **Install Pulumi Dependencies:**

   ```bash
   pulumi install
   ```

   This command ensures that Pulumi recognizes and utilizes the Poetry-managed environment.

### Step 3: Customize the Configuration

1. **Update Configuration Files:**

   - Customize the `.env` file with your project-specific environment variables.
   - Adjust the Pulumi configuration files under `.pulumi` to match your cloud and infrastructure setup.

2. **Set Up Your Pulumi Stack:**

   Configure your Pulumi stack settings to match your project environment by running:

   ```bash
   pulumi stack init dev
   ```

   Replace `dev` with your desired stack name.

3. **Install Pyright for Type Checking:**

   We enforce strict type checking using [Pyright](https://github.com/microsoft/pyright).

   **Add Pyright to the Development Dependencies:**

   ```bash
   poetry add --dev pyright
   ```

   **Configure Pyright:**

   Create a `pyrightconfig.json` in the project root to define Pyright settings:

   ```json
   {
     "include": ["**/*.py"],
     "exclude": ["**/__pycache__/**"],
     "reportMissingImports": true,
     "pythonVersion": "3.8",
     "typeCheckingMode": "strict"
   }
   ```

   **Verify Type Checking:**

   ```bash
   poetry run pyright
   ```

4. **Editor Integration (Optional):**

   For real-time type checking and enhanced development experience, integrate Pyright with your editor. If you use Visual Studio Code, install the [Pylance extension](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) and set `"python.analysis.typeCheckingMode": "strict"` in your settings.

### Step 4: Start Developing

1. **Deploy the Infrastructure:**

   Before deploying, ensure that your code passes type checking to maintain code quality.

   **Run Type Checking:**

   ```bash
   poetry run pyright
   ```

   **Deploy with Pulumi:**

   ```bash
   pulumi up
   ```

   If type errors are detected, the deployment will halt, and errors will be displayed.

2. **Implement Best Practices:**

   - Use `TypedDict` to define resource inputs with type hints, enhancing code readability and type safety.
   - Follow the code standards and guidelines outlined in [PULUMI_PYTHON.md](docs/PULUMI_PYTHON.md), including naming conventions, type annotations, and error handling.
   - Organize your code into logical modules and packages for better maintainability.

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

- **Keep Your Dependencies Up to Date:** Regularly update the tools and libraries used in your project.
- **Enforce Type Checking:** Use Pyright to catch type errors early in the development process.
- **Document Your Changes:** Update the README and other documentation as your project evolves.
- **Engage with the Community:** Join the [ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX) to get support and share your experiences.

## How-To (Boilerplate Instructions)

This repository is designed to be used as a template for new DevOps projects. Follow the steps below to clone and configure your environment.

### Prerequisites

Ensure you have the following tools and accounts:

1. [GitHub](https://github.com)
2. [Pulumi Cloud](https://app.pulumi.com/signup)
3. [Microsoft Edge](https://www.microsoft.com/en-us/edge) or [Google Chrome](https://www.google.com/chrome)
4. [Poetry](https://python-poetry.org/docs/#installation)

### Quickstart

Follow these steps to get your environment up and running:

1. **Clone the Repository:**

   Clone this repository to your GitHub account using the "Use this template" button.

2. **Launch in GitHub Codespaces or Local Development Environment:**

   - **GitHub Codespaces:** Start a new Codespace with the following options:

     - **Branch:** `main`
     - **Dev Container Configuration:** `konductor`
     - **Region:** Your choice
     - **Machine Type:** 4 cores, 16 GB RAM, or better

   - **Local Development:** Set up your local environment using Docker or your preferred method.

3. **Open the Integrated Terminal:**

   Use `Ctrl + `` to open the VSCode integrated terminal.

4. **Initialize the Development Environment:**

   **Install Dependencies:**

   ```bash
   poetry install
   ```

   **Activate the Virtual Environment:**

   ```bash
   poetry shell
   ```

5. **Authenticate Credentials:**

   Login to Pulumi Cloud and other required services.

   ```bash
   pulumi login
   ```

6. **Configure the Pulumi Stack:**

   Set up Pulumi stack parameters.

   ```bash
   pulumi stack init dev
   ```

   Replace `dev` with your desired stack name.

7. **Run Type Checking:**

   Ensure your code passes type checking before deployment.

   ```bash
   poetry run pyright
   ```

8. **Deploy the Infrastructure:**

   **Deploy with Pulumi:**

   ```bash
   pulumi up
   ```

9. **Cleanup:**

   Clean up all Kubernetes and Pulumi resources when you're done.

   ```bash
   pulumi destroy
   ```

## Contributing

Contributions are welcome! This template is intended to evolve with the needs of the community. Learn how to contribute by reading our [CONTRIBUTING.md](https://github.com/ContainerCraft/Konductor/issues/22).

### Developing and Testing

Use the `act` tool to test GitHub Actions locally before pushing your changes.

```bash
act
```

## Community and Support

Join our community to discuss, learn, and contribute:

- **[ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX)**
- **[Konductor Project FAQ](FAQ.md)**
