# Konductor AWS Module

The **Konductor AWS Module** extends the foundational principles established by the Konductor Core Module to the Amazon Web Services (AWS) ecosystem. By leveraging a set of well-defined Pydantic models, strict validation rules, DRY patterns, and the global compliance and metadata frameworks established in the core, the AWS module ensures that AWS-specific infrastructure can be deployed and managed consistently, securely, and in full alignment with organizational standards.

This README provides an overview of the AWS module’s purpose, architecture, and integration points. For detailed type definitions and technical references, consult the AWS Module’s types documentation (e.g., `TYPES.md`) and the Konductor Core Module documentation.

## Table of Contents

1. [Introduction](#introduction)
2. [Purpose and Scope](#purpose-and-scope)
3. [Core Integration and Provider-Specific Focus](#core-integration-and-provider-specific-focus)
4. [Foundational AWS Data Models](#foundational-aws-data-models)
5. [Compliance, Security, and Networking](#compliance-security-and-networking)
6. [EKS and Kubernetes Integration](#eks-and-kubernetes-integration)
7. [IAM and Tenant Management](#iam-and-tenant-management)
8. [Global Metadata, Tags, and Labels](#global-metadata-tags-and-labels)
9. [Usage and Configuration Guidelines](#usage-and-configuration-guidelines)
10. [Extensibility and Future-Proofing](#extensibility-and-future-proofing)
11. [Related Documentation and Resources](#related-documentation-and-resources)
12. [Conclusion](#conclusion)

## Introduction

The Konductor AWS Module brings provider-specific capabilities into the Konductor IaC platform. Built on top of the core module’s provider-agnostic design patterns, it enables reliable, secure, and compliant provisioning of AWS infrastructure. Every configuration—from low-level VPC CIDR assignments to EKS cluster setups—adheres to the same core principles of strict typing, compliance enforcement, and metadata-driven governance.

## Purpose and Scope

**What the AWS Module Does:**

- Focuses on AWS as a primary cloud provider target within Konductor’s multi-cloud strategy.
- Implements AWS-centric configuration models (e.g., `AWSConfig`) that integrate seamlessly with core abstractions.
- Handles common AWS resources (VPCs, subnets, EKS clusters, IAM users) while maintaining consistency and compliance.
- Provides specialized fields and validations (such as allowed AWS regions, proper CIDR formatting, and valid EKS versions).

**What It Does Not Do:**

- It does not bypass or replace the core module’s principles. Instead, it extends them into AWS-specific domains.
- It does not implement high-level application logic. Instead, it provides foundational building blocks for infrastructure.
- It does not manage non-AWS providers directly, though it may produce outputs (like Kubernetes providers) that other modules can consume.

## Core Integration and Provider-Specific Focus

The AWS module inherits the base classes and compliance frameworks from the Konductor Core Module. This ensures that:

- **Consistency in Configuration**: All AWS configurations (`AWSConfig`) follow patterns established in `BaseConfigModel`.
- **Shared Compliance**: Compliance requirements like FISMA, NIST, and ATO are integrated at the AWS layer, just as they are at the core, ensuring production stacks meet rigorous standards.
- **Global Metadata Alignment**: AWS resources benefit from globally applied tags, labels, and annotations, enabling cross-platform observability and uniform governance.

This provider-specific focus ensures that building AWS resources is as seamless and maintainable as working with any other provider within Konductor.

## Foundational AWS Data Models

The AWS module introduces AWS-specific configuration types designed to integrate cleanly with the core models:

- **`AWSConfig`**: Central configuration model for AWS deployments. Defines the AWS region, optional profile, account ID, and references to other sub-configurations like `network`, `security`, and `eks`.
- **`NetworkConfig`**: Governs VPC creation, subnet CIDRs, NAT gateways, and flow logs. Strict validators ensure proper CIDR notation.
- **`SecurityConfig`**: Centralizes AWS security services (Security Hub, GuardDuty, AWS Config, CloudTrail) and KMS management.
- **`IAMUserConfig`**: Provides consistent, validated fields for IAM user creation, including paths, policies, and permissions boundaries.

All models follow Pydantic’s strict typing and validation, ensuring misconfigurations are caught early.

## Compliance, Security, and Networking

Compliance and security remain first-class citizens in the AWS module:

- **Compliance**: Leverage `ComplianceConfig` from the core. Ensure that AWS-specific constructs align with required frameworks. For example, production stacks must be fully authorized before provisioning resources.
- **Security**: Activate and configure AWS Security Hub, GuardDuty, AWS Config, CloudTrail, and KMS key policies through `SecurityConfig`. These ensure that governance, auditing, and threat detection are inherent parts of the infrastructure stack.
- **Networking**: Define a standardized, validated network structure via `NetworkConfig`. Enforce correct CIDR blocks, structured AZ usage, and optional NAT/VPN gateways. This creates a secure, compliant foundation for AWS-hosted workloads.

## EKS and Kubernetes Integration

The AWS module can provision and manage Amazon EKS clusters:

- **`EksConfig` and `EksClusterConfig`**: Specify cluster names, Kubernetes versions, endpoint visibility (public/private), and node groups.
- **Validated Versions**: Kubernetes versions are validated against a supported list, ensuring compatibility and stability.
- **Kubernetes Provider Integration**: Once EKS clusters are provisioned, the AWS module can return a corresponding Kubernetes provider object. This enables downstream modules—such as those managing cluster add-ons, workloads, or CI/CD pipelines—to consume the Kubernetes provider seamlessly.
- **Consistent Metadata**: EKS clusters inherit global tags, labels, and annotations, integrating them into the broader compliance and governance frameworks.

This approach empowers a unified workflow: build the EKS cluster with AWS module settings, then rely on core patterns or other modules to apply configurations and resources inside Kubernetes.

## IAM and Tenant Management

Beyond EKS and networking, the AWS module supports AWS-specific identity and account structures:

- **`IAMUserConfig`**: Create IAM users with consistent patterns for naming, email assignment, and policies. Enforce best practices like including a permissions boundary and stable tagging.
- **`TenantAccountConfig`**: Define tenant accounts for multi-account strategies, setting clear boundaries and OU placements. This aligns with organizational policies while still embracing the DRY, validated approach.

This ensures a secure and well-structured account and identity landscape aligned with the larger compliance narrative.

## Global Metadata, Tags, and Labels

As with the core module, global metadata fields are consistently applied:

- **`CommonMetadataFields`**: Ensures tags, labels, and annotations follow a unified schema. Every AWS resource inherits these fields.
- **Consistent Application**: AWS resources become easily discoverable, traceable, and auditable by virtue of standardized metadata. This supports operations, compliance audits, and cost allocation.

## Usage and Configuration Guidelines

To use the AWS module effectively:

1. **Start with Core Abstractions**: Begin by defining your `ComplianceConfig` and `InitializationConfig` in the core. Ensure you have a strong, validated base before proceeding to AWS specifics.
2. **Enable AWS and Configure Fields**: In your Pulumi stack configuration, provide the `aws` block with `region`, `network`, `security`, `eks`, and other fields as needed.
3. **Validate Early, Fail Fast**: Pydantic validation catches invalid CIDRs, unsupported regions, or incomplete compliance settings. Address these proactively.
4. **Leverage Compliance**: For production stacks, ensure `ComplianceConfig` is properly set to enforce authorized deployments.
5. **Consume Outputs**: Use the AWS module’s output (e.g., EKS cluster providers) as inputs to other modules. This encourages a composable, layered approach to IaC, where AWS lays the foundation and other modules build upon it.

## Extensibility and Future-Proofing

The AWS module’s adherence to core patterns and Pydantic models fosters scalability and adaptability:

- **Easy Integration of New AWS Services**: Add new resource types or configurations by extending `AWSConfig` or creating new dedicated models, confident that they will integrate smoothly with existing patterns.
- **Consistent Compliance and Security**: Any new resource or service inherits established compliance checks and metadata standards.
- **Multi-Provider Harmony**: Even as you embrace AWS, the architecture remains open to other providers. The AWS module fits into a larger multi-cloud strategy without special exceptions.

## Related Documentation and Resources

- [Core Module Documentation](../core/README.md) for foundational models and compliance.
- [Developer Guide](../../developer_guide/README.md) for standards on code style, documentation, and contribution.
- [Pulumi Python Development Standards](../../developer_guide/pulumi-python.md) for best practices on coding within this ecosystem.
- [TYPES.md](TYPES.md) (planned or existing) for detailed AWS type references.
