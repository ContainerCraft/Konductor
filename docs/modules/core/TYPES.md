# Core Module Types

Welcome to the **Core Module Types** reference. This document provides a detailed explanation of the `core/types` module, which defines foundational data models, interfaces, and configurations used throughout the Konductor codebase. These types form the backbone of our Infrastructure as Code (IaC), enabling a consistent, secure, and maintainable approach to Platform Engineering with Pulumi.

This guide is suitable for engineers at all levels, from those new to the project and Pulumi, to experienced Staff and Principal-level engineers looking to leverage these abstractions effectively. By understanding these core types, you will be better equipped to design, implement, and extend the Konductor IaC to meet your own requirements.

## Table of Contents

1. [Introduction](#introduction)
2. [Core Principles and Conventions](#core-principles-and-conventions)
3. [Exceptions](#exceptions)
4. [Git Metadata: `GitInfo`](#git-metadata-gitinfo)
5. [Compliance Configuration](#compliance-configuration)
   - [Ownership and ATO Information](#ownership-and-ato-information)
   - [FISMA and NIST Compliance](#fisma-and-nist-compliance)
   - [Project Configuration](#project-configuration)
   - [Creating Compliance Configurations from Pulumi](#creating-compliance-configurations-from-pulumi)
6. [Resource and Configuration Base Types](#resource-and-configuration-base-types)
   - [ResourceBase](#resourcebase)
   - [ConfigBase](#configbase)
   - [InitializationConfig](#initializationconfig)
   - [ModuleRegistry](#moduleregistry)
   - [ModuleBase](#modulebase)
7. [Module Deployment Results and Interfaces](#module-deployment-results-and-interfaces)
   - [ModuleDeploymentResult](#moduledeploymentresult)
   - [DeploymentContext Protocol](#deploymentcontext-protocol)
   - [ModuleInterface Protocol](#moduleinterface-protocol)
8. [Metadata Singleton](#metadata-singleton)
9. [Initialization Configuration Protocol: `InitConfig`](#initialization-configuration-protocol-initconfig)
10. [Global Metadata Setup](#global-metadata-setup)
11. [Configuration Management with `ConfigManager`](#configuration-management-with-configmanager)
12. [Global Metadata and Stack Config Types](#global-metadata-and-stack-config-types)
    - [GlobalMetadata](#globalmetadata)
    - [SourceRepository](#sourcerepository)
    - [StackConfig](#stackconfig)
    - [StackOutputs](#stackoutputs)
    - [ModuleDefaults](#moduledefaults)
    - [ResourceMetadata](#resourcemetadata)
13. [Example Stack Outputs](#example-stack-outputs)
14. [Best Practices and Usage Guidelines](#best-practices-and-usage-guidelines)
15. [Conclusion](#conclusion)
16. [Related Documentation](#related-documentation)

## Introduction

The `core/types` module provides foundational data models essential for defining and managing infrastructure resources, configuration, compliance requirements, and module metadata within the Konductor platform. These types are implemented using Pythonic best practices, Pydantic models for validation, and Pulumi-native patterns for IaC. By leveraging these carefully curated types, teams can ensure that their deployments are secure, consistent, and compliant with organizational and industry standards.

## Core Principles and Conventions

- **Type Safety**: All types enforce strict typing with no use of `Any`, ensuring robust IDE support, static analysis, and reducing runtime errors.
- **Pydantic Validation**: Use of Pydantic ensures that configuration and resource definitions are validated early, preventing incorrect deployments.
- **Compliance and Security**: Compliance-oriented fields, such as ATO details and FISMA/NIST configurations, ensure that resources meet stringent security and governance requirements.
- **Pulumi-Native Patterns**: Integration points and protocols are designed to fit into the Pulumi ecosystem, enabling state-based IaC workflows and stack configuration management.
- **Modularity and Clarity**: Classes and interfaces are logically separated. For example, `ResourceBase` centralizes common resource attributes, and `InitializationConfig` standardizes how stacks initialize with required data.

## Exceptions

- **CoreError**: The base exception class for the core module.
- **ModuleLoadError**: Raised when a module cannot be loaded due to configuration errors or missing dependencies.

These exceptions help isolate and clearly communicate issues within the core module’s loading and configuration processes.

## Git Metadata: `GitInfo`

**Class:** `GitInfo`

Stores information about the Git repository state at deployment time:

- **Fields:**
  - `commit_hash`: The current Git commit hash of the deployed code.
  - `branch_name`: The branch name at deployment time.
  - `remote_url`: The remote repository URL.

**Use Case:**  
Embed Git metadata into resource tags or stack outputs for traceability. For example, tagging resources with commit hashes can help identify which code version deployed a particular piece of infrastructure.

## Compliance Configuration

Compliance is integral to the Konductor platform. The core module includes types dedicated to capturing compliance metadata from Pulumi stack configurations and embedding it into resource metadata.

### Ownership and ATO Information

- **OwnershipInfo** and **ProjectOwnership**: Typed dictionaries defining ownership contact information for both owner and operations teams.
- **AtoConfig**: Captures Authority to Operate (ATO) information, including `authorized`, `eol` (end-of-life), and `last_touch` timestamps.  
  This ensures that production environments must have explicit authorization details before deployments proceed.

### FISMA and NIST Compliance

- **FismaConfig**: Describes the FISMA compliance level and mode (e.g., `moderate` level, `warn` mode).
- **NistConfig**: Details NIST compliance controls, listing auxiliary controls and exceptions.

### Project Configuration

- **ProjectConfig**: Defines the environment (e.g., `prod-us-west`), production flag, ownership details, and providers used. This ensures clarity on which environment resources belong to and what compliance posture to enforce.

### Creating Compliance Configurations from Pulumi

**Class:** `ComplianceConfig`  
Use the classmethod `from_pulumi_config()` to automatically instantiate a `ComplianceConfig` from stack configurations. If a production environment is detected, required fields (like `authorized`) must be present.

This ensures that compliance is not optional. If required compliance data is missing, a default, well-defined compliance configuration is created and logged.

## Resource and Configuration Base Types

### ResourceBase

**Class:** `ResourceBase`

Defines the fundamental attributes of any infrastructure resource managed via Pulumi:

- **name**: The resource’s logical name.
- **urn**: The Pulumi URN (Uniform Resource Name) identifying the resource.
- **id**: Provider-assigned ID.
- **metadata**: Dict containing `tags`, `labels`, and `annotations`.
- **created_at**: ISO timestamp of resource creation.

By centralizing these fields, all resources gain consistent tagging and annotation capabilities, aiding governance, traceability, and observability.

### ConfigBase

**Class:** `ConfigBase`

Provides common configuration fields for modules, including:

- **enabled**: Whether the module or feature is active.
- **parent** and **dependencies**: Hierarchy and dependency definition.
- **configuration**: User-defined dictionary of config parameters.
- **metadata**: Additional labels and annotations applied to the configuration.

### InitializationConfig

**Class:** `InitializationConfig`

Extends `ConfigBase` to handle core stack initialization details:

- **pulumi_config**: Access to Pulumi configuration objects.
- **stack_name** and **project_name**: Identifiers for the stack and project.
- **global_depends_on**: A list of resources that must be deployed before this module.
- **platform_providers**: References to cloud providers or other platforms.
- **git_info** and **compliance_config**: Embeds Git and compliance data at initialization time.
- **deployment_date_time** and **deployment_manager**: Track deployment context for auditing and integration with external systems.

Validation ensures all configurations are dictionaries, preventing malformed inputs.

### ModuleRegistry

**Class:** `ModuleRegistry`

Records module registration info:

- **name**, **parent**, **dependencies**: Describes how modules relate to each other within the stack.

### ModuleBase

**Class:** `ModuleBase`

Represents deployable infrastructure units (modules):

- **name**, **enabled**, **parent**, **dependencies**, **config**, **metadata**: Standard set of fields to manage lifecycle, dependencies, and configuration of modules.

## Module Deployment Results and Interfaces

### ModuleDeploymentResult

**Class:** `ModuleDeploymentResult`

Captures the outcome of deploying a module:

- **success**: Whether the deployment succeeded.
- **config**: A list of `ResourceBase` configurations produced.
- **compliance**: Compliance and traceability information.
- **resources**: Mapping of resource identifiers to their instances.
- **errors**: Any errors encountered during deployment.
- **metadata**: Additional metadata about the deployment.

This structure helps downstream consumers understand what changed and what resources were created or updated.

### DeploymentContext Protocol

**Interface:** `DeploymentContext`

A protocol defining how to interact with the deployment environment:

- `get_config() -> ConfigBase`: Retrieve configuration used during deployment.
- `deploy() -> ModuleDeploymentResult`: Execute the deployment and return results.

This abstraction allows modules to work with various deployment contexts uniformly.

### ModuleInterface Protocol

**Interface:** `ModuleInterface`

Specifies the lifecycle methods for modules:

- `validate_config()`, `validate_resources()`, `pre_deploy_check()`
- `deploy(ctx: DeploymentContext) -> ModuleDeploymentResult`
- `post_deploy_validation()`
- `get_dependencies()`

These methods ensure that modules follow a consistent pattern of validation, dependency checking, deployment, and post-deployment validation.

## Metadata Singleton

**Class:** `MetadataSingleton`

A thread-safe global store for cross-module metadata, including global tags, labels, and annotations. This helps ensure consistent metadata application across modules, consolidating data like Git metadata, compliance info, and global annotations in one place.

## Initialization Configuration Protocol: `InitConfig`

**Interface:** `InitConfig`

A protocol that defines the shape of initial configuration needed to set up global metadata. It includes `project_name`, `stack_name`, `git_info`, and `metadata`. The `setup_global_metadata()` function relies on this protocol to populate global metadata via `MetadataSingleton`.

## Global Metadata Setup

**Function:** `setup_global_metadata(init_config: InitConfig)`

Populates global tags, labels, annotations, and git metadata by merging global context from `InitConfig`. This step standardizes all resources with consistent global metadata, aiding in compliance, governance, and traceability.

## Configuration Management with `ConfigManager`

**Class:** `ConfigManager`

Handles caching and retrieving Pulumi stack configuration:

- `get_config()`: Retrieves the entire configuration.
- `get_module_config(module_name)`: Gets configuration for a specific module.
- `get_enabled_modules()`: Lists modules with `enabled = True`.

This class supports dynamic and modular configuration, making it easy to load and adapt configurations across multiple modules and environments.

## Global Metadata and Stack Config Types

### GlobalMetadata

**Class:** `GlobalMetadata`

Encapsulates global resource tags, labels, and annotations applied at the stack level. This supports platform-wide governance and consistent labeling strategies.

### SourceRepository

**Class:** `SourceRepository`

Captures source control details (branch, commit, remote URL, and optional tag) for auditing and compliance. Useful for rollbacks, audits, and ensuring reproducible infrastructure states.

### StackConfig and StackOutputs

**Classes:** `StackConfig` and `StackOutputs`

- **StackConfig**: Combines `compliance`, `metadata`, `source_repository`, and other configuration details into a coherent top-level model representing the entire stack’s configuration.
- **StackOutputs**: Represents the final aggregated outputs after a deployment, potentially including `secrets` for sensitive data storage. This can be shared with other teams, CI/CD pipelines, or auditing tools.

### ModuleDefaults

**Class:** `ModuleDefaults`

Specifies a baseline configuration for modules, providing default `enabled` and `config` values. Useful for ensuring a consistent starting point for new modules.

### ResourceMetadata

**Class:** `ResourceMetadata`

Extends `ResourceBase` to add fields like `tags`, `labels`, `annotations`, and `updated_at`. This ensures resources not only have creation timestamps but can also track updates and extended metadata easily.

## Example Stack Outputs

The provided `stack_outputs.json` exemplifies how all these configuration and metadata constructs come together in a final stack output. Compliance data, global metadata, source repository information, and module-specific details appear harmoniously, offering deep visibility and full traceability into your deployed infrastructure.

## Best Practices and Usage Guidelines

- **Always Validate Configurations**: Use the `from_pulumi_config()` methods and Pydantic validation to catch errors early.
- **Tagging and Labeling**: Leverage `MetadataSingleton` and `GlobalMetadata` to ensure consistent labeling for governance and compliance.
- **Keep Modules Small and Focused**: `ModuleBase` and related interfaces encourage modular design. Keep modules focused on specific tasks.
- **Regularly Update Compliance Data**: Update `ComplianceConfig` as regulatory requirements change, ensuring continuous compliance.
- **Embrace Protocols**: `ModuleInterface` and `DeploymentContext` provide patterns that ensure modules are easy to test, mock, and integrate.

## Conclusion

The `core/types` module is the cornerstone for building a secure, compliant, and maintainable IaC ecosystem within the Konductor platform. By understanding and using these types, you empower your team to deliver high-quality, enterprise-grade infrastructure consistently and transparently.

Whether you are a Junior Engineer just starting out, or a Principal Engineer leading large-scale initiatives, these core types enable a unified approach to infrastructure management that is both accessible and powerful.

## Related Documentation

- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Development Standards (pulumi-python.md)](../docs/developer_guide/pulumi-python.md)
- [Types Hierarchy Guide](../developer_guide/Types_Hierarchy.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)

