# COMPLIANCE.md

---

## Table of Contents

1. [Introduction](#introduction)
2. [Motivation](#motivation)
3. [Compliance Strategy](#compliance-strategy)
   - [Objectives](#objectives)
   - [Key Innovations](#key-innovations)

4. [Implementation Details](#implementation-details)
   - [Compliance Metadata Management](#compliance-metadata-management)
   - [Automatic Propagation Mechanism](#automatic-propagation-mechanism)
   - [Resource Tagging and Labeling](#resource-tagging-and-labeling)
   - [Configuration Schema](#configuration-schema)
   - [Version Management](#version-management)
   - [Stack Outputs and Reporting](#stack-outputs-and-reporting)

5. [Developer Expectations and Best Practices](#developer-expectations-and-best-practices)
   - [Module Autonomy](#module-autonomy)
   - [Integration with Compliance Framework](#integration-with-compliance-framework)
   - [Coding Standards](#coding-standards)

6. [User Experience (UX)](#user-experience-ux)
   - [Simplified Configuration](#simplified-configuration)
   - [Deployment Workflow](#deployment-workflow)
   - [Validation and Error Handling](#validation-and-error-handling)

7. [Business Stakeholder Value](#business-stakeholder-value)
   - [Accelerated Time-to-Compliance](#accelerated-time-to-compliance)
   - [Auditability and Transparency](#auditability-and-transparency)
   - [Risk Reduction](#risk-reduction)

8. [Conclusion](#conclusion)
9. [Appendix](#appendix)
   - [Glossary](#glossary)
   - [References](#references)

---

## Introduction

This document outlines the comprehensive compliance strategy implemented in the **Konductor Infrastructure as Code (IaC) Template Repository**. It details how the codebase is designed to **reduce the time necessary to achieve production-ready compliance and authority to operate**, while also minimizing the overhead associated with compliance maintenance and renewal audits. The document serves as a benchmark and guiding framework for developing and maintaining compliance features within the Konductor IaC codebase.

---

## Motivation

In the modern regulatory landscape, organizations face increasing pressure to comply with various standards such as **NIST**, **FISMA**, **ISO 27001**, and industry-specific regulations like **HIPAA** and **PCI DSS**. Achieving and maintaining compliance is often a resource-intensive process due to:

- **Complexity of Compliance Requirements**: Navigating overlapping and evolving regulations.
- **Dynamic Infrastructure**: Rapid changes in cloud environments and deployment practices.
- **High Audit Costs**: Significant time and financial resources required for compliance audits and renewals.
- **Human Error Risk**: Manual processes increase the likelihood of misconfigurations leading to non-compliance.
- **Muddy Compliance Traceability**: Difficulty in tracking compliance status across multiple environments and resources.

**Our Goal**: To **innovate** within the IaC domain by creating a codebase that automates compliance tasks, reduces human error, and provides a clear path to achieving and maintaining compliance with minimal overhead.

---

## Compliance Strategy

### Objectives

1. **Automate Compliance Integration**: Embed compliance controls and metadata into the IaC workflow.
2. **Modular Autonomy**: Allow module maintainers to define and manage compliance aspects within their specialty areas.
3. **Centralized Compliance Metadata**: Collect and manage compliance-related information centrally for consistency and ease of access.
4. **Simplify Auditing Processes**: Provide comprehensive outputs that facilitate easy auditing and reporting.
5. **Enhance Developer and User Experience**: Reduce the complexity and mental overhead associated with compliance tasks.

### Key Innovations

- **Pydantic-Based Configuration Models**: Utilizing Pydantic for type-safe, validated configurations that allow for complex, nested compliance metadata.
- **Automatic Propagation of Compliance Metadata**: Implementing mechanisms to automatically propagate compliance intent through resource tags, labels, and annotations across all providers.
- **Dynamic Module Integration**: Enabling modules to autonomously define their compliance requirements while integrating seamlessly with the core compliance framework.
- **Comprehensive Stack Outputs**: Aggregating compliance data into easily consumable outputs for both technical and non-technical stakeholders.

---

## Implementation Details

### Compliance Metadata Management

**Centralized Metadata Collection**:

- **Configuration Dictionaries**: Compliance-related metadata is defined in a central configuration file (e.g., `Pulumi.<stack>.yaml`) under a dedicated `compliance` section.
- **Metadata Types**:
   - **Regulatory Controls**: NIST, FISMA, ISO control identifiers.
   - **Component Versions**: Versions of deployed components and dependencies.
   - **Source Control Information**: Git repository URLs, commit hashes, branches.
   - **Identity Information**: Cloud provider identities (e.g., AWS STS `GetCallerIdentity`, Kubernetes User and Service Account, etc. outputs).
   - **Organizational Metadata**: Owner information, environment tags, project identifiers.

**Example Configuration**:

```yaml
config:
  compliance:
    nist:
      controls:
        - "AC-2"
        - "IA-5"
      exceptions:
        - "AC-2(1)"
        - "IA-5(1)"
    fisma:
      level: "moderate"
    iso_27001:
      controls:
        - "A.9.2.3"
        - "A.11.2.1"
      controls: []
    organization: "magic-science-team"
    environment: "production"
    owner: "compliance-team@nasa.com"
    project_id: "proj-12345"
```

### Automatic Propagation Mechanism

**Mechanism Overview**:

- **Metadata Injection**: Compliance metadata is injected into resources during their creation within each module.
- **Uniform Interfaces**: Modules interact with compliance metadata through standardized interfaces provided by the core codebase.
- **Dynamic Discovery**: Modules dynamically discover compliance configurations relevant to them, promoting autonomy and flexibility.

**Technical Implementation**:

- **Core Compliance Module** (`core/compliance.py`):
   - Provides functions to access compliance metadata.
   - Supplies utility functions to format and apply metadata to resources.

- **Module Integration**:
   - Modules import the core compliance utilities.
   - Apply compliance metadata during resource instantiation.

**Example in Module Deployment**:

```python
from core.compliance import get_compliance_tags

def deploy_aws_module(
        config: AWSConfig,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> pulumi.Resource:
    aws_provider = providers.get('aws')
    compliance_tags = get_compliance_tags()
    s3_bucket = aws.s3.Bucket(
        resource_name='my_bucket',
        bucket='my-unique-bucket-name',
        tags=compliance_tags,
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=global_depends_on,
        )
    )
    return s3_bucket
```

### Resource Tagging and Labeling

**AWS Resources**:

- Tags are applied to resources using the `tags` argument.
- Supports tagging for resources like EC2 instances, S3 buckets, Lambda functions, etc.

**Kubernetes Resources**:

- Labels and annotations are applied to resources via the `metadata` field.
- Useful for compliance-related labeling in deployments, services, pods, etc.

**Example Tags and Labels**:

- **Tags**:
   - `compliance:nist-controls=AC-2,IA-5`
   - `compliance:owner=compliance-team@example.com`
   - `compliance:project-id=proj-12345`

- **Labels**:
   - `compliance/nist-controls: "AC-2,IA-5"`
   - `compliance/owner: "compliance-team@example.com"`
   - `compliance/project-id: "proj-12345"`

### Configuration Schema

**Pydantic Models**:

- Each module defines its configuration schema using Pydantic models (`types.py`), which include compliance-related fields as needed.
- Validation ensures that compliance metadata adheres to expected formats and values.

**Example Pydantic Model**:

```python
from pydantic import BaseModel, Field

class ComplianceConfig(BaseModel):
    nist_controls: List[str] = Field(default_factory=list)
    fisma_moderate: bool = False
    iso_27001_controls: List[str] = Field(default_factory=list)
    organization: str
    environment: str
    owner: str
    project_id: str
```

### Version Management

**Module Versioning**:

- **Kubernetes Modules**: Utilize version locking mechanisms to ensure specific versions of Helm charts and resources are deployed.
- **Cloud Provider Modules**: Rely on SDK versions specified in `requirements.txt`; internal version management within configurations is unnecessary.

**Version Reporting**:

- Component versions are collected and included in compliance metadata.
- Enables traceability and auditing of deployed component versions.

### Stack Outputs and Reporting

**Aggregated Outputs**:

- Compliance metadata, configuration details, and versions are aggregated and exposed via stack outputs.
- Outputs are structured in a way that is consumable by both technical tools and non-technical stakeholders.

**Example Stack Output**:

```bash
pulumi stack output compliance_report
```

```json
{
  "nist_controls": ["AC-2", "IA-5"],
  "fisma": {
    "moderate": true,
  },
  "iso_27001_controls": ["A.9.2.3", "A.11.2.1"],
  "organization": "magic-science-team",
  "environment": "production",
  "owner": "compliance-team@example.com",
  "project_id": "proj-12345",
  "component_versions": {
    "aws": "3.40.0",
    "kubernetes": "2.8.0",
    "cert_manager": "v1.5.3"
  },
  "source_control": {
    "repository": "https://github.com/magic-science-team/fork-konductor-template-to-make-new-proj",
    "branch": "main",
    "commit": "abc123def456"
  },
  "identity": {
    "aws_account_id": "123456789012",
    "aws_user_arn": "arn:aws:iam::123456789012:user/DeployUser"
  }
}
```

**Reporting Tools Integration**:

- Stack outputs can be consumed by reporting tools, compliance dashboards, or exported to formats like CSV, JSON, or integrated with SIEM systems.
- Facilitates automated compliance checks and monitoring.

---

## Developer Expectations and Best Practices

### Module Autonomy

- **Specialty Ownership**: Module maintainers have full authority over their module's configuration structure and implementation.
- **Compliance Integration**: Modules are expected to integrate compliance metadata according to the standards provided by the core compliance framework.

### Integration with Compliance Framework

- **Accessing Compliance Metadata**: Modules should use the core compliance utilities to access and apply compliance metadata.
- **Consistent Application**: Ensure that compliance metadata is applied uniformly across all resources within the module.
- **Validation**: Leverage Pydantic models to validate compliance-related configurations.

**Example**:

```python
from core.compliance import get_compliance_annotations

def deploy_kubernetes_module(
        config: KubernetesConfig,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> pulumi.Resource:
    k8s_provider = providers.get('k8s')
    compliance_annotations = get_compliance_annotations()
    deployment = k8s.apps.v1.Deployment(
        resource_name='my_app',
        metadata={
            'name': 'my-app',
            'annotations': compliance_annotations,
        },
        spec={
            # Deployment spec...
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=global_depends_on,
        )
    )
    return deployment
```

### Coding Standards

- **Type Annotations**: Use type hints and Pydantic models for configurations.
- **Documentation**: Document compliance integration points in module `README.md` files.
- **Error Handling**: Provide clear error messages for compliance-related validation errors.
- **Avoid Hardcoding**: Do not hardcode compliance metadata; always use the centralized configurations.

---

## User Experience (UX)

### Simplified Configuration

- **Single Source of Truth**: Users define compliance configurations in one place, reducing complexity.
- **Default Values**: Sensible defaults are provided, minimizing the required input from users.
- **Validation Feedback**: Immediate validation feedback helps users correct configurations before deployment.

### Deployment Workflow

- **Seamless Integration**: Compliance features are integrated into the deployment workflow without additional steps.
- **Visibility**: Users can view applied compliance metadata through resource tags, labels, and stack outputs.
- **Customization**: Users can customize compliance settings to fit their organizational requirements.

### Validation and Error Handling

- **Pydantic Validation**: Configurations are validated using Pydantic, ensuring type safety and correctness.
- **Clear Error Messages**: Users receive detailed error messages that pinpoint configuration issues.
- **Examples and Documentation**: Modules provide examples and documentation to guide users in configuring compliance settings.

---

## Business Stakeholder Value

### Accelerated Time-to-Compliance

- **Reduced Implementation Time**: Automation of compliance tasks speeds up the deployment process.
- **Pre-Built Compliance Controls**: Out-of-the-box compliance integrations reduce the need for custom development.
- **Quick Adaptation**: Ability to quickly adapt to new compliance requirements by updating configurations.

### Auditability and Transparency

- **Comprehensive Reporting**: Stack outputs provide a complete picture of compliance status.
- **Traceability**: Source control and version metadata enable tracking of changes over time.
- **Evidence for Audits**: Resource tags and labels serve as evidence of compliance measures in place.

### Risk Reduction

- **Minimized Human Error**: Automated compliance reduces the risk of misconfigurations leading to non-compliance.
- **Consistent Application**: Ensures compliance controls are applied uniformly across all infrastructure components.
- **Regulatory Alignment**: Simplifies alignment with regulatory requirements, reducing the risk of penalties or sanctions.

---

## Conclusion

The Konductor IaC codebase embodies a strategic approach to compliance management by integrating compliance considerations into every layer of the infrastructure provisioning process. By leveraging innovative techniques such as Pydantic for configuration validation and automatic propagation of compliance metadata, we have significantly reduced the time and effort required to achieve and maintain compliance. This not only accelerates the path to production-ready deployments but also provides business stakeholders with the tools and transparency needed for effective compliance governance.

---

## Appendix

### Glossary

- **IaC (Infrastructure as Code)**: The practice of managing and provisioning infrastructure through machine-readable definition files, rather than physical hardware configuration or interactive configuration tools.
- **NIST (National Institute of Standards and Technology)**: A U.S. federal agency that develops and promotes measurement, standards, and technology.
- **FISMA (Federal Information Security Management Act)**: U.S. legislation that defines a comprehensive framework to protect government information, operations, and assets.
- **ISO 27001**: An international standard for managing information security.
- **Pydantic**: A Python library for data parsing and validation using Python type annotations.
- **SDK (Software Development Kit)**: A collection of software development tools in one installable package.

### References

- **NIST Cybersecurity Framework**: [https://www.nist.gov/cyberframework](https://www.nist.gov/cyberframework)
- **FISMA Compliance**: [https://csrc.nist.gov/topics/laws-and-regulations/laws/fisma](https://csrc.nist.gov/topics/laws-and-regulations/laws/fisma)
- **ISO/IEC 27001 Information Security Management**: [https://www.iso.org/isoiec-27001-information-security.html](https://www.iso.org/isoiec-27001-information-security.html)
- **Pulumi Documentation**: [https://www.pulumi.com/docs/](https://www.pulumi.com/docs/)
- **Pydantic Documentation**: [https://pydantic-docs.helpmanual.io/](https://pydantic-docs.helpmanual.io/)
- __AWS STS GetCallerIdentity__: [https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html)

---

**Note**: This document serves as a living reference for the compliance strategy within the Konductor IaC codebase. It should be updated as new compliance requirements emerge and as the codebase evolves to meet the changing needs of the organization and regulatory landscape.
