# Account Vending Machine (AVM) Implementation Guide

## Introduction

This document provides a comprehensive guide to implementing an **Account Vending Machine (AVM)** within the AWS Module of the Konductor project. The AVM automates the provisioning of AWS accounts at scale, ensuring consistent application of security controls, compliance requirements, and organizational policies. This guide is intended for developers and platform engineers responsible for scaling AWS infrastructure to support over 300 accounts for various science cloud teams.

---

## Table of Contents

1. [Overview](#overview)
2. [Objectives](#objectives)
3. [Technical Architecture](#technical-architecture)
4. [Implementation Steps](#implementation-steps)
   - 4.1 [AVM Workflow](#avm-workflow)
   - 4.2 [Configuration Management](#configuration-management)
   - 4.3 [Automation Scripts](#automation-scripts)
   - 4.4 [Integration with AWS Control Tower](#integration-with-aws-control-tower)
5. [Security and Compliance](#security-and-compliance)
6. [Tagging and Metadata Propagation](#tagging-and-metadata-propagation)
7. [Testing and Validation](#testing-and-validation)
8. [Operational Considerations](#operational-considerations)
9. [Future Enhancements](#future-enhancements)
10. [References](#references)

---

## Overview

An **Account Vending Machine (AVM)** is an automated system that provisions AWS accounts in a standardized, scalable, and secure manner. It is a critical component for organizations managing a large number of AWS accounts, enabling self-service account creation while enforcing governance policies and compliance requirements.

The AVM integrates with AWS Organizations and AWS Control Tower to automate account provisioning, configuration, and policy enforcement. It ensures that new accounts are set up consistently, with the necessary security controls, compliance settings, and resource configurations applied from the outset.

---

## Objectives

- **Automate Account Provisioning**: Enable rapid, automated creation of AWS accounts to support over 300 science cloud teams.
- **Ensure Compliance**: Apply compliance controls and security policies consistently across all accounts.
- **Standardize Configurations**: Enforce standardized resource configurations and tagging strategies.
- **Facilitate Self-Service**: Provide a self-service mechanism for authorized users to request new accounts.
- **Integrate with Existing Infrastructure**: Seamlessly integrate the AVM into the existing AWS module and infrastructure codebase.

---

## Technical Architecture

### Core Components

1. **Account Provisioning Service**: A service (e.g., Lambda function) that automates the creation of new AWS accounts using the AWS Organizations API.
2. **Request Interface**: A mechanism (e.g., Service Catalog, API Gateway, or web portal) for users to request new accounts.
3. **Configuration Templates**: Predefined templates that include standard configurations, policies, and compliance settings to be applied to new accounts.
4. **Automation Orchestration**: Use of AWS Step Functions or similar services to orchestrate the account creation workflow.
5. **Notification and Approval System**: Integration with AWS SNS, AWS SQS, or third-party tools to handle approval workflows and notifications.

### Architectural Diagram

```plaintext
+---------------------+       +----------------------+       +-----------------------+
|                     |       |                      |       |                       |
|   User Interface    +------->  Account Provisioning +------->  AWS Organizations   |
|  (API or Portal)    |       |      Service         |       |       and Control     |
|                     |       |                      |       |          Tower        |
+---------------------+       +----------------------+       +-----------------------+
                                    |
                                    v
                          +-------------------+
                          |                   |
                          |  Configuration    |
                          |     Templates     |
                          |                   |
                          +-------------------+
```

---

## Implementation Steps

### 4.1 AVM Workflow

1. **Account Request**: An authorized user submits a request for a new AWS account via the user interface.
2. **Validation and Approval**: The request is validated, and approval is obtained if necessary.
3. **Account Creation**: The Account Provisioning Service creates a new AWS account using AWS Organizations.
4. **Configuration Application**: Standard configurations, policies, and compliance settings are applied to the new account.
5. **Resource Provisioning**: Optional resources (e.g., VPCs, IAM roles) are provisioned in the new account.
6. **Notification**: The requester is notified of the account creation and provided with access details.

### 4.2 Configuration Management

- **Templates**: Use Infrastructure as Code (IaC) templates (e.g., Pulumi, CloudFormation) to define standard configurations.
- **Parameterization**: Allow templates to accept parameters for customization while enforcing mandatory configurations.
- **Version Control**: Store templates in a version-controlled repository to manage changes and rollbacks.

### 4.3 Automation Scripts

- **Account Creation Function**: Develop a function (e.g., AWS Lambda) that interfaces with AWS Organizations to create accounts.

  ```python
  import boto3

  def create_aws_account(account_name, email, role_name, iam_user_access_to_billing):
      client = boto3.client('organizations')
      response = client.create_account(
          AccountName=account_name,
          Email=email,
          RoleName=role_name,
          IamUserAccessToBilling=iam_user_access_to_billing
      )
      return response['CreateAccountStatus']
  ```

- **Workflow Orchestration**: Use AWS Step Functions to manage the sequence of tasks, including account creation, configuration, and notification.

### 4.4 Integration with AWS Control Tower

- **Landing Zone Setup**: Utilize AWS Control Tower to set up a landing zone, providing guardrails and baseline configurations.
- **Account Factory**: Leverage the AWS Control Tower Account Factory to provision accounts with standardized blueprints.
- **Customizations for Control Tower (CfCT)**: Implement customizations using CfCT to apply additional configurations and resources.

---

## Security and Compliance

- **Service Control Policies (SCPs)**: Automatically attach SCPs to new accounts to enforce governance policies.
- **IAM Role Provisioning**: Create IAM roles and permission boundaries in new accounts to enforce least privilege.
- **Compliance Tagging**: Apply compliance-related tags during account provisioning for tracking and auditing.
- **Logging and Monitoring**: Enable CloudTrail, AWS Config, and GuardDuty in new accounts for security monitoring.

---

## Tagging and Metadata Propagation

- **Standardized Tagging**: Apply global tags, compliance tags, and metadata tags as defined in the AWS module.
- **Metadata Integration**: Propagate metadata (e.g., git commit, build number) to the new accounts and resources.
- **Cost Allocation Tags**: Include tags to facilitate cost tracking and allocation across accounts.

---

## Testing and Validation

- **Unit Testing**: Test individual functions, such as account creation and configuration application, using mocks.
- **Integration Testing**: Simulate the end-to-end account provisioning process in a test environment.
- **Security Testing**: Validate that security controls and compliance settings are correctly applied.
- **Scalability Testing**: Test the AVM's ability to handle multiple account provisioning requests concurrently.

---

## Operational Considerations

- **Approval Workflow**: Implement an approval process for account requests, possibly integrating with IAM Identity Center or third-party tools.
- **Error Handling**: Include robust error handling and retries in the automation scripts.
- **Notifications**: Configure notifications for account provisioning status, using AWS SNS or email.
- **Access Management**: Define processes for providing access credentials to new account owners securely.
- **Logging**: Maintain logs of all account provisioning activities for auditing purposes.

---

## Future Enhancements

- **Self-Service Portal**: Develop a web-based portal for users to request and manage AWS accounts.
- **Integration with ITSM Tools**: Connect the AVM with IT Service Management tools for ticketing and workflows.
- **Automated Resource Provisioning**: Extend the AVM to provision common resources (e.g., S3 buckets, databases) in new accounts.
- **Policy-as-Code Enforcement**: Implement policy checks using tools like AWS Config Rules or Open Policy Agent (OPA) during account provisioning.
- **Multi-Cloud Support**: Explore extending the AVM concept to support account provisioning in other cloud providers.

---

## References

- [AWS Organizations API Reference](https://docs.aws.amazon.com/organizations/latest/APIReference/Welcome.html)
- [AWS Control Tower Account Factory](https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html)
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [Customizations for AWS Control Tower (CfCT)](https://docs.aws.amazon.com/controltower/latest/userguide/customizations.html)
- [AWS Service Catalog](https://docs.aws.amazon.com/servicecatalog/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Konductor AWS Module Developer Guide](./developer_guide.md)
- [Konductor AWS Module Implementation Roadmap](./implementation_roadmap.md)
- [Konductor Core Module Documentation](../../../modules/core/README.md)

---

**Note**: This guide is intended to be a living document. As the implementation progresses and new requirements emerge, this document should be updated accordingly to reflect the latest design decisions and best practices.
