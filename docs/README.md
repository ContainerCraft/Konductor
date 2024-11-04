# Konductor Documentation

Welcome to the Konductor documentation! This comprehensive guide covers everything you need to know about using, developing for, and contributing to the Konductor Infrastructure as Code (IaC) platform.

## Introduction

Konductor is a powerful Infrastructure as Code (IaC) platform built on Pulumi and Python, designed to streamline DevOps workflows and Platform Engineering practices. Whether you're a platform user deploying infrastructure, a developer contributing modules, or a maintainer managing the project, you'll find the information you need in these docs.

## Documentation Structure

Our documentation is organized into several main sections, each targeting specific user needs:

### 🚀 [Getting Started](./getting_started.md)
Quick-start guide to help you begin using Konductor, including installation, basic setup, and your first deployment.

### 📚 User Documentation
- [User Guide](./user_guide/README.md): Complete guide for platform users
- [Module Documentation](./modules/README.md): Detailed guides for individual modules
- [FAQ & Troubleshooting](./user_guide/faq_and_troubleshooting.md): Common issues and solutions

### 💻 Developer Documentation
- [Developer Guide](./developer_guide/README.md): Guide for contributing to Konductor
- [Module Development](./developer_guide/modules/README.md): Creating and maintaining modules
- [Contribution Guidelines](./developer_guide/contribution_guidelines.md): How to contribute

### 📖 Reference Documentation
- [Pulumi Python Standards](./reference/PULUMI_PYTHON.md): Development standards and practices
- [TypedDict Guide](./reference/TypedDict.md): Using TypedDict for configurations
- [Style Guide](./reference/style_guide.md): Documentation and code style standards

### ⚖️ Compliance & Planning
- [Compliance Guide](./compliance/COMPLIANCE.md): Compliance standards and implementation
- [Project Roadmap](./roadmaps/ROADMAP.md): Future development plans
- [Roadmap Addendum](./roadmaps/ROADMAP_Addendum.md): Additional planning details

## Available Modules

Konductor includes several core modules, each with comprehensive documentation:

### AWS Module
- [User Guide](./modules/aws/README.md)
- [Developer Guide](./developer_guide/modules/aws/README.md)
- [Implementation Roadmap](./developer_guide/modules/aws/implementation_roadmap.md)
- [EKS Setup Guide](./developer_guide/modules/aws/eks_donor_template.md)
- [OpenTelemetry Integration](./developer_guide/modules/aws/eks_opentelemetry_docs.md)

### Cert Manager Module
- [User Guide](./modules/cert_manager/README.md)
- [Developer Guide](./developer_guide/modules/cert_manager/README.md)
- [Installation Guide](./modules/cert_manager/installation_guide.md)

## Contributing

We welcome contributions from the community! To get started:

1. Read our [Contribution Guidelines](./developer_guide/contribution_guidelines.md)
2. Check our [Issue Template](./contribution_templates/issue_template.md)
3. Review our [Pull Request Template](./contribution_templates/pull_request_template.md)
4. See our [Feature Request Template](./contribution_templates/feature_request_template.md)

## Accessibility

This documentation adheres to web accessibility guidelines to ensure it's usable by everyone:

- Clear heading hierarchy for easy navigation
- Alt text for all images and diagrams
- High contrast text and proper font sizing
- Keyboard-navigable interface
- Screen reader compatibility

## Getting Help

If you need assistance:

1. Check the [FAQ & Troubleshooting](./user_guide/faq_and_troubleshooting.md) guide
2. Search existing [GitHub Issues](https://github.com/containercraft/konductor/issues)
3. Join our [Community Discord](https://discord.gg/Jb5jgDCksX)
4. Create a new issue using our [Issue Template](./contribution_templates/issue_template.md)

## Documentation Updates

This documentation is continuously improved based on user feedback and project evolution. To suggest improvements:

1. Create an issue using our documentation issue template
2. Submit a pull request with your proposed changes
3. Join the documentation discussions in our community channels

## License

This documentation and the Konductor project are licensed under [LICENSE]. See the [LICENSE](../LICENSE) file for details.
