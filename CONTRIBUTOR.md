# Contributing to Konductor

Thank you for considering contributing to the Konductor project! Your contributions help improve the platform and empower the community. This guide provides all the information you need to contribute effectively and harmoniously.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Submitting Pull Requests](#submitting-pull-requests)
4. [Development Guidelines](#development-guidelines)
   - [Coding Standards](#coding-standards)
   - [Commit Messages](#commit-messages)
   - [Documentation Standards](#documentation-standards)
5. [Community Guidelines](#community-guidelines)
6. [Governance and Decision-Making](#governance-and-decision-making)
7. [Licensing](#licensing)
8. [Acknowledgments](#acknowledgments)
9. [Contact Information](#contact-information)

---

## Code of Conduct

Our community is dedicated to providing an inclusive and harassment-free experience for everyone. We expect all contributors to adhere to our [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## Getting Started

### Prerequisites

To contribute to the Konductor project, ensure you have the following installed:

- **Visual Studio Code (VSCode)**: [Download VSCode](https://code.visualstudio.com/)
- **Remote Development Extension Pack**: Install via the [VSCode Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)
- **Docker Desktop or Docker CLI**: [Install Docker](https://docs.docker.com/get-docker/)

### Setting Up the Development Environment

The Konductor project utilizes the ContainerCraft Devcontainer to provide a consistent and fully-configured development environment. Follow these steps to get started:

1. **Fork the Repository**

   Click the "Fork" button at the top of the [Konductor GitHub repository](https://github.com/konductor/konductor) to create your own fork.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/your-username/konductor.git
   ```

3. **Open the Project in VSCode**

   Launch VSCode and open the cloned `konductor` directory.

   Or in terminal:

   ```bash
   code konductor
   ```

4. **Reopen in Container**

   Upon opening the folder, VSCode should detect the `.devcontainer` configuration and prompt you to reopen the project in the container.

   - If prompted, click **"Reopen in Container"**.
   - If not prompted, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac) and select **"Remote-Containers: Reopen in Container"**.

5. **Wait for the Container to Build and Start**

   VSCode will build the devcontainer image if necessary and start the container. This may take a few minutes on the first run.

6. **Start Developing**

   Once the devcontainer is running, you can start coding immediately. All dependencies are installed, and tools like Pulumi and Poetry are configured.

---

## How to Contribute

### Reporting Bugs

If you encounter a bug, please help us by reporting it:

1. **Search Existing Issues**

   Before opening a new issue, check if it has already been reported.

2. **Open a New Issue**

   - Navigate to the [Issues](https://github.com/konductor/konductor/issues) page.
   - Click "New Issue" and select "Bug Report".
   - Provide a clear and descriptive title.
   - Include steps to reproduce, expected behavior, and screenshots if applicable.

3. **Security Vulnerabilities**

   If you discover a security vulnerability, **do not** open an issue. Instead, contact us directly at [emcee@braincraft.io](mailto:emcee@braincraft.io).

### Suggesting Enhancements

We welcome suggestions to improve Konductor:

1. **Search Existing Discussions**

   Check if your idea has been discussed or is in progress.

2. **Open a New Issue**

   - Go to the [Issues](https://github.com/konductor/konductor/issues) page.
   - Click "New Issue" and select "Feature Request".
   - Describe your enhancement clearly, including the problem it solves.

### Submitting Pull Requests

We appreciate your contributions via pull requests (PRs):

1. **Create a Branch**

   Use descriptive names:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**

   - Follow the [Coding Standards](#coding-standards).
   - Include tests for new functionality.
   - Update documentation as needed.

3. **Commit Changes**

   ```bash
   git add .
   git commit -m "feat(module): add new feature description"
   ```

4. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**

   - Navigate to your fork on GitHub.
   - Click "Compare & pull request".
   - Provide a clear description of your changes.
   - Link to any relevant issues.

6. **Respond to Feedback**

   Be responsive to code review comments and requests for changes.

---

## Development Guidelines

### Coding Standards

- **PEP 8 Compliance**: Adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
- **Type Annotations**: Use type hints throughout the code.
- **Naming Conventions**:
  - Variables and functions: `snake_case`
  - Classes and exceptions: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Imports**: Organize imports into three sections: standard library, third-party, and local imports.
- **Linters and Formatters**:
  - Use **Black** for code formatting.
  - Use **Flake8** for linting.
  - Use **Pyright** for type checking.

### Commit Messages

- **Format**: Use the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- **Structure**:

  \```
  type(scope): subject

  body (optional)

  footer (optional)
  \```

- **Types**:
  - `feat`: New feature
  - `fix`: Bug fix
  - `docs`: Documentation changes
  - `style`: Code style changes (formatting, missing semi-colons, etc.)
  - `refactor`: Code refactoring without changing functionality
  - `test`: Adding or updating tests
  - `chore`: Maintenance tasks

- **Example**:

  \```
  feat(storage): add S3 bucket encryption

  Enable default encryption for all S3 buckets created in the storage module.

  Closes #123
  \```

### Documentation Standards

- **Docstrings**: Use docstrings for all modules, classes, and functions.
- **Markdown**: Write documentation in Markdown format.
- **Style Guide**: Follow the [Documentation Style Guide](./docs/developer_guide/documentation.md).
- **Comments**: Use comments to explain complex logic, but avoid unnecessary comments for self-explanatory code.

---

## Community Guidelines

- **Respectful Communication**: Be kind and considerate in all interactions.
- **Inclusivity**: Embrace diversity and strive to include all voices.
- **Collaboration**: Encourage and support new contributors.
- **Responsiveness**: Aim to respond to issues and PRs in a timely manner.
- **Learning Environment**: Foster an atmosphere where learning and growth are encouraged.

---

## Governance and Decision-Making

- **Core Maintainers**: A group responsible for project stewardship.
- **Decision Process**:
  - **Consensus Seeking**: Aim for agreement among contributors.
  - **Proposal Submission**: Significant changes should be proposed via issues or discussions.
  - **Review and Feedback**: Open for community input before final decisions.
- **Meetings**: Periodic meetings may be held and are open to all contributors.
- **Conflict Resolution**: Address disagreements constructively, seeking mediation if necessary.

---

## Licensing

By contributing to Konductor, you agree that your contributions will be licensed under the [Adaptive Public License 1.0](./LICENSE). This ensures that the project remains free and open-source, benefiting the entire community.

---

## Acknowledgments

We appreciate every contributor who invests time and effort into making Konductor better. Your contributions, whether through code, documentation, testing, or discussions, are invaluable.

Special thanks to:

- **Early Contributors**: For laying the foundation of the project.
- **Community Members**: For active participation and feedback.
- **Open-Source Projects**: Whose tools and libraries we rely on.

---

## Contact Information

- **Email**: [emcee@braincraft.io](mailto:emcee@braincraft.io)
- **Discord**: [Konductor](https://discord.gg/VR9UhMrcFW)
- **GitHub Discussions**: Engage in conversations on our [GitHub Discussions](https://github.com/konductor/konductor/discussions) page.

---

We look forward to your contributions and are excited to have you as part of the Konductor community!
