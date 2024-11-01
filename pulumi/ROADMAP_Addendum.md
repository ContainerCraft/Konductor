# Konductor IaC Template Repository Refactor and Enhancement Roadmap

> **Technical Blueprint Addendum**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Introduction](#introduction)
3. [Objectives](#objectives)
4. [Current State Analysis](#current-state-analysis)
5. [Proposed Solution](#proposed-solution)
   - [Part 1: Aligning AWS Module with Kubernetes Modules](#part-1-aligning-aws-module-with-kubernetes-modules)
   - [Part 2: Modular Version Handling](#part-2-modular-version-handling)
   - [Part 3: Enhancing Configuration Management with Pydantic](#part-3-enhancing-configuration-management-with-pydantic)

6. [Detailed Implementation Plan](#detailed-implementation-plan)
   - [Part 1 Implementation Steps](#part-1-implementation-steps)
   - [Part 2 Implementation Steps](#part-2-implementation-steps)
   - [Part 3 Implementation Steps](#part-3-implementation-steps)

7. [Technical Considerations](#technical-considerations)
   - [Dependency Management](#dependency-management)
   - [Error Handling and Logging](#error-handling-and-logging)
   - [Testing Strategy](#testing-strategy)
   - [Documentation Standards](#documentation-standards)
   - [Security Implications](#security-implications)

8. [Risks and Mitigations](#risks-and-mitigations)
9. [Timeline and Milestones](#timeline-and-milestones)
10. [Conclusion](#conclusion)
11. [Appendices](#appendices)
   - [Appendix A: Pydantic Overview](#appendix-a-pydantic-overview)
   - [Appendix B: Code Samples](#appendix-b-code-samples)
   - [Appendix C: Glossary](#appendix-c-glossary)

---

## Executive Summary

This technical document outlines a comprehensive plan to refactor and enhance the Konductor Infrastructure as Code (IaC) codebase. The primary goals are to align the AWS module with the existing Kubernetes modules, implement modular version handling, and improve configuration management using Pydantic. By executing this plan, we aim to achieve consistency, improve maintainability, and enhance the developer and user experience. This document is intended for the principal engineers leading the project and includes detailed technical explanations and code examples to guide the implementation.

---

## Introduction

Konductor is an IaC platform built using Pulumi and Python, designed to streamline DevOps workflows and Platform Engineering practices. As the codebase has evolved, inconsistencies have emerged, particularly between the AWS module and the Kubernetes modules. This document proposes a refactoring plan to address these inconsistencies and introduces Pydantic for robust configuration management.

---

## Objectives

- **Consistency**: Standardize the module structure and deployment logic across all modules, including AWS.
- **Modular Version Handling**: Limit version locking mechanisms to Kubernetes modules where necessary.
- **Enhanced Configuration Management**: Utilize Pydantic for type-safe, validated, and flexible configurations.
- **Extensibility**: Prepare the codebase for future support of additional cloud providers (e.g., GCP, Azure).
- **Maintainability**: Improve code readability and reduce technical debt.
- **Developer and User Experience**: Provide clear documentation, error messages, and consistent patterns.

---

## Current State Analysis

### Kubernetes Modules

- **Structure**:
   - Reside under `pulumi/modules/<module_name>/`.
   - Include `types.py`, `deploy.py`, and `README.md`.
   - Use `dataclasses` for configuration models.
   - Deployment functions have consistent signatures and return types.

- **Version Handling**:
   - Version locking mechanisms are in place.
   - Versions are managed via configuration.

### AWS Module

- **Structure**:
   - Does not conform to the standard module structure.
   - Lacks separation of concerns (configuration vs. deployment logic).
   - Deployment function signatures differ from Kubernetes modules.

- **Version Handling**:
   - Unnecessary version interfaces are present.
   - Versions are managed via `requirements.txt`, making internal version handling redundant.

### Issues Identified

- **Inconsistency** in module structures and deployment patterns.
- **Redundant Version Handling** in cloud provider modules.
- **Complex Configuration Management** lacking type safety and validation.
- **Integration Challenges** due to divergent module implementations.

---

## Proposed Solution

### Part 1: Aligning AWS Module with Kubernetes Modules

- **Restructure the AWS module** to match the directory and code organization of Kubernetes modules.
- **Standardize deployment function signatures** and remove unnecessary version handling.
- **Integrate the AWS module into the core deployment process** using dynamic module discovery.

### Part 2: Modular Version Handling

- **Restrict version locking mechanisms** to Kubernetes modules where applicable.
- **Remove version interfaces** from cloud provider modules (AWS, GCP, Azure).
- **Adjust core configuration and deployment functions** to handle versioning exclusively for Kubernetes modules.

### Part 3: Enhancing Configuration Management with Pydantic

- **Integrate Pydantic** for robust configuration models with validation.
- **Allow each module to define its own configuration schema** independently.
- **Centralize configuration loading and validation** in the core module.
- **Improve error reporting and documentation** for configurations.

---

## Detailed Implementation Plan

### Part 1 Implementation Steps

#### Step 1: Restructure AWS Module Directory

**Action**: Move all AWS module files under `pulumi/modules/aws/`.

**Technical Details**:

- **Create Directory**:
   - Ensure `pulumi/modules/aws/` exists.

- **Organize Files**:
   - Move existing AWS code files (`aws_deploy.py`, `aws_types.py`, etc.) into `pulumi/modules/aws/`.
   - Rename files to `deploy.py` and `types.py` to match the convention.

- **Initialize Module**:
   - Add `__init__.py` to `pulumi/modules/aws/`.

**Expected Outcome**:

- The AWS module directory mirrors the structure of Kubernetes modules.
- All AWS-related code is encapsulated within the module directory.

#### Step 2: Define Configuration Data Classes in `types.py`

**Action**: Create `AWSConfig` class in `pulumi/modules/aws/types.py` without a `version` attribute.

**Technical Details**:

- **Use Pydantic**:

   - Import `BaseModel` from `pydantic`.

- **Define Configuration Class**:

```python
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any

class AWSConfig(BaseModel):
    enabled: bool = False
    profile: Optional[str] = None
    region: str
    account_id: Optional[str] = None
    landingzones: List[Dict[str, Any]] = Field(default_factory=list)

    @root_validator
    def validate_region(cls, values):
        if not values.get('region'):
            raise ValueError('The "region" field is required for AWSConfig.')
        return values
```

- **Explanation**:

   - `enabled`: Determines if the module is active.
   - `profile`: AWS CLI profile.
   - `region`: Required AWS region.
   - `account_id`: Optional AWS account ID.
   - `landingzones`: List of landing zone configurations.
   - `validate_region`: Ensures `region` is provided.

**Expected Outcome**:

- A type-safe, validated configuration model for the AWS module.

#### Step 3: Update Deployment Logic in `deploy.py`

__Action__: Create `deploy_aws_module` function in `pulumi/modules/aws/deploy.py` with a consistent signature.

**Technical Details**:

- **Define Deployment Function**:

```python
from typing import List, Dict, Any
import pulumi
import pulumi_aws as aws
from .types import AWSConfig

def deploy_aws_module(
        config: AWSConfig,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> pulumi.Resource:
    aws_provider = providers.get('aws')
    if not aws_provider:
        raise ValueError("AWS provider not found.")

    # Example AWS resource creation
    s3_bucket = aws.s3.Bucket(
        resource_name='my_bucket',
        bucket='my-unique-bucket-name',
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=global_depends_on,
        )
    )

    return s3_bucket
```

- **Explanation**:

   - The function signature aligns with other modules.
   - It accepts the validated `config` object.
   - Uses the `aws_provider` from the `providers` dictionary.
   - Returns the primary resource without version information.

**Expected Outcome**:

- AWS module deployment logic conforms to the standard pattern.
- Version handling is removed from the AWS module.

#### Step 4: Modify `__main__.py` to Include AWS Module

__Action__: Update `pulumi/__main__.py` to deploy the AWS module consistently.

**Technical Details**:

- **Initialize AWS Provider**:

```python
# Inside main function
aws_config, aws_enabled = get_module_config('aws', config)
aws_provider = None
if aws_enabled:
    from pulumi_aws import Provider as AWSProvider
    aws_provider = AWSProvider(
        'aws_provider',
        profile=aws_config.profile,
        region=aws_config.region,
    )
```

- **Update Providers Dictionary**:

```python
providers = {
    'k8s': k8s_provider,
    'aws': aws_provider,
    # Add other providers as needed
}
```

- **Include AWS Module in Deployment**:

```python
modules_to_deploy = [
    'aws',
    # Other modules...
]
```

**Expected Outcome**:

- `__main__.py` treats the AWS module like other modules.
- AWS provider is initialized and passed to the deployment function.

#### Step 5: Adjust `core/deployment.py` to Handle Providers and Versioning

__Action__: Modify `deploy_module` to handle modules with and without versioning.

**Technical Details**:

- __Update `deploy_module` Function__:

```python
def deploy_module(
    module_name: str,
    config: pulumi.Config,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]]
) -> None:
    config_obj, module_enabled = get_module_config(module_name, config)

    if module_enabled:
        deploy_func = discover_deploy_function(module_name)
        result = deploy_func(
            config=config_obj,
            global_depends_on=global_depends_on,
            providers=providers,
        )

        if module_name in KUBERNETES_MODULES:
            version, primary_resource = result
            versions[module_name] = version
        else:
            primary_resource = result

        configurations[module_name] = {"enabled": module_enabled}
        global_depends_on.append(primary_resource)
    else:
        log.info(f"Module {module_name} is not enabled.")
```

- **Explanation**:

   - Checks if the module is enabled.
   - For Kubernetes modules, expects a `(version, resource)` tuple.
   - For other modules, expects a single resource.
   - Updates `versions` only for Kubernetes modules.

**Expected Outcome**:

- `deploy_module` can handle both versioned and non-versioned modules.

### Part 2 Implementation Steps

#### Step 6: Update `core/config.py` to Handle Versioning Exclusively for Kubernetes Modules

__Action__: Adjust `get_module_config` to inject version information only for Kubernetes modules.

**Technical Details**:

- **Define Kubernetes Modules List**:

```python
KUBERNETES_MODULES = [
    'cert_manager',
    'kubevirt',
    'multus',
    # Other Kubernetes modules...
]
```

- __Update `get_module_config` Function__:

```python
def get_module_config(
        module_name: str,
        config: pulumi.Config,
    ) -> Tuple[Any, bool]:
    module_config_dict = config.get_object(module_name) or {}
    module_enabled = module_config_dict.get('enabled', False)

    # Inject version for Kubernetes modules
    if module_name in KUBERNETES_MODULES:
        default_versions = load_default_versions()
        module_config_dict['version'] = module_config_dict.get('version', default_versions.get(module_name))

    # Import and instantiate the module's configuration class
    # ... (same as before)
```

- **Explanation**:

   - Only Kubernetes modules receive a `version` in their configuration.
   - Non-Kubernetes modules are unaffected.

**Expected Outcome**:

- Version handling is exclusive to Kubernetes modules.

#### Step 7: Adjust Module Discovery Functions

__Action__: Ensure `discover_config_class` and `discover_deploy_function` work for all modules.

**Technical Details**:

- __Update `discover_config_class`__:

```python
def discover_config_class(module_name: str) -> Type[BaseModel]:
    types_module = importlib.import_module(f"modules.{module_name}.types")
    for name, obj in inspect.getmembers(types_module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            return obj
    raise ValueError(f"No Pydantic BaseModel found in modules.{module_name}.types")
```

- __Update `discover_deploy_function`__:

```python
def discover_deploy_function(module_name: str) -> Callable:
    deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
    function_name = f"deploy_{module_name}_module"
    deploy_function = getattr(deploy_module, function_name, None)
    if not deploy_function:
        raise ValueError(f"No deploy function named '{function_name}' found in modules.{module_name}.deploy")
    return deploy_function
```

**Expected Outcome**:

- Module discovery functions can handle any module following the standard structure.

#### Step 8: Remove Version Handling from Cloud Provider Modules

**Action**: Remove any version-related code from cloud provider modules.

**Technical Details**:

- **In `types.py`**:
   - Ensure no `version` field is present.

- **In `deploy.py`**:
   - Ensure deployment functions do not return version information.
   - Remove any logic related to version checking or handling.

**Expected Outcome**:

- Cloud provider modules (AWS, GCP, Azure) are free of unnecessary version handling code.

#### Step 9: Optional - Load Versions from `requirements.txt`

**Action**: Implement a utility to extract versions from `requirements.txt` for logging purposes.

**Technical Details**:

- **Utility Function**:

```python
def get_module_version_from_requirements(module_name: str) -> Optional[str]:
    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                if module_name in line:
                    parts = line.strip().split('==')
                    if len(parts) == 2:
                        return parts[1]
    except Exception as e:
        pulumi.log.warn(f"Error reading requirements.txt: {e}")
    return None
```

- **Usage**:

   - For logging or documentation, not for configuration.

**Expected Outcome**:

- Ability to report the versions of cloud provider SDKs in use.

### Part 3 Implementation Steps

#### Step 10: Integrate Pydantic into the Project

**Action**: Add Pydantic to the project dependencies.

**Technical Details**:

- **Install Pydantic**:

```bash
pip install pydantic
```

- **Update `requirements.txt`**:

```
pydantic>=1.8.2
```

**Expected Outcome**:

- Pydantic is available for use in the codebase.

#### Step 11: Define Base Configuration Classes

__Action__: Create `BaseConfig` in `pulumi/core/base_config.py` for common fields.

**Technical Details**:

- **Define `BaseConfig`**:

```python
from pydantic import BaseModel

class BaseConfig(BaseModel):
    enabled: bool = False
```

- **Explanation**:

   - Provides a common `enabled` field.
   - Modules can inherit from `BaseConfig`.

**Expected Outcome**:

- A foundational configuration class for modules to extend.

#### Step 12: Update Module Configuration Models to Use Pydantic

**Action**: Update `types.py` in each module to define Pydantic models.

**Technical Details**:

- **For AWS Module**:

```python
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any

class AWSConfig(BaseConfig):
    profile: Optional[str] = None
    region: str
    account_id: Optional[str] = None
    landingzones: List[Dict[str, Any]] = Field(default_factory=list)

    @root_validator
    def validate_region(cls, values):
        if not values.get('region'):
            raise ValueError('The "region" field is required for AWSConfig.')
        return values
```

- **For Kubernetes Module**:

```python
class CertManagerConfig(BaseConfig):
    version: str = "latest"
    namespace: str = "cert-manager"
    install_crds: bool = True
```

**Expected Outcome**:

- Module configurations are now type-safe and validated using Pydantic.

#### Step 13: Centralize Configuration Loading and Validation

__Action__: Update `get_module_config` in `core/config.py` to use Pydantic models.

**Technical Details**:

- **Update Function**:

```python
def get_module_config(
        module_name: str,
        config: pulumi.Config,
    ) -> Tuple[Any, bool]:
    module_config_dict = config.get_object(module_name) or {}
    module_enabled = module_config_dict.get('enabled', False)

    if module_name in KUBERNETES_MODULES:
        default_versions = load_default_versions()
        module_config_dict['version'] = module_config_dict.get('version', default_versions.get(module_name))

    types_module = importlib.import_module(f"modules.{module_name}.types")
    ModuleConfigClass = getattr(types_module, f"{module_name.capitalize()}Config")

    try:
        config_obj = ModuleConfigClass(**module_config_dict)
    except ValidationError as e:
        pulumi.log.error(f"Configuration error in module '{module_name}':\n{e}")
        raise

    return config_obj, module_enabled
```

**Expected Outcome**:

- Configurations are loaded and validated centrally, reducing duplication.

#### Step 14: Update Deployment Functions to Use Validated Configurations

**Action**: Modify deployment functions to accept the Pydantic `config` object.

**Technical Details**:

- **Example for AWS Module**:

```python
def deploy_aws_module(
        config: AWSConfig,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> pulumi.Resource:
    aws_provider = providers.get('aws')
    if not aws_provider:
        raise ValueError("AWS provider not found.")

    # Use configuration values directly
    # Example: region = config.region
    # ...

    # Deployment logic
    # ...
```

**Expected Outcome**:

- Deployment functions operate on validated, type-safe configurations.

#### Step 15: Provide Clear Error Reporting

**Action**: Ensure validation errors are clearly reported to the user.

**Technical Details**:

- __In `get_module_config`__:

```python
except ValidationError as e:
    pulumi.log.error(f"Configuration error in module '{module_name}':\n{e}")
    raise
```

- **User Feedback**:

```
Configuration error in module 'aws':
1 validation error for AWSConfig
region
  The "region" field is required for AWSConfig. (type=value_error)
```

**Expected Outcome**:

- Users receive immediate and actionable feedback on configuration issues.

#### Step 16: Document Configuration Schemas

**Action**: Update `README.md` for each module to reflect the new configuration schemas.

**Technical Details**:

- **Include Configuration Examples**:

```markdown
## Configuration Schema

```yaml
aws:
  enabled: true
  profile: "default"
  region: "us-west-2"
  # Other fields...
```

```

```

- **Explain Each Field**:

   - **enabled**: Enables or disables the module.
   - **profile**: AWS CLI profile name.
   - **region**: AWS region (required).
   - __account_id__: AWS account ID.
   - **landingzones**: List of landing zone configurations.

**Expected Outcome**:

- Users have clear guidance on how to configure each module.

---

## Technical Considerations

### Dependency Management

- **Pydantic Version**: Ensure compatibility with the Python version in use.
- **Pulumi Providers**: Keep cloud provider SDKs up to date via `requirements.txt`.

### Error Handling and Logging

- **Consistent Logging**: Use `pulumi.log` for logging messages.
- **Exception Handling**: Catch and handle exceptions at appropriate levels.

### Testing Strategy

- **Unit Tests**: Write tests for configuration models and deployment functions.
- **Integration Tests**: Test module deployments in sandbox environments.
- **Continuous Integration**: Implement CI pipelines to automate testing.

### Documentation Standards

- **Docstrings**: Use Google or NumPy style for functions and classes.
- **Inline Comments**: Explain complex logic within the code.
- **Module `README.md`**: Provide comprehensive documentation for each module.

### Security Implications

- **Sensitive Data Handling**: Ensure that sensitive information is not logged or exposed.
- **Configuration Validation**: Prevent invalid configurations that could lead to security vulnerabilities.

---

## Risks and Mitigations

- **Risk**: Breaking Changes During Refactoring
   - **Mitigation**: Implement changes incrementally and test thoroughly.

- **Risk**: Incompatibility with Existing Configurations
   - **Mitigation**: Provide migration guides and support legacy configurations temporarily.

- **Risk**: Learning Curve for Pydantic
   - **Mitigation**: Provide training and resources for the development team.

---

## Timeline and Milestones

1. **Week 1**:
   - Integrate Pydantic into the project.
   - Update `core/config.py` and base classes.

2. **Week 2**:
   - Refactor AWS module to align with Kubernetes modules.
   - Remove version handling from cloud provider modules.

3. **Week 3**:
   - Update Kubernetes modules to use Pydantic.
   - Adjust core deployment functions.

4. **Week 4**:
   - Comprehensive testing and bug fixing.
   - Update documentation and provide training.

5. **Week 5**:
   - Final review and deployment to production.
   - Post-deployment monitoring and support.

---

## Conclusion

This technical roadmap provides a detailed plan for refactoring and enhancing the Konductor IaC codebase. By aligning module structures, implementing modular version handling, and integrating Pydantic for configuration management, we address current inconsistencies and set the foundation for future growth. The detailed steps and technical considerations outlined in this document are intended to guide the principal engineers leading the project through a successful implementation.

---

## Appendices

### Appendix A: Pydantic Overview

Refer to the [Pydantic documentation](https://pydantic-docs.helpmanual.io/) for comprehensive information on features and usage.

### Appendix B: Code Samples

Detailed code samples are provided within the implementation steps above.

### Appendix C: Glossary

- **IaC (Infrastructure as Code)**: Managing and provisioning computing infrastructure through machine-readable definition files.
- **Pulumi**: An IaC tool that allows you to define cloud resources using programming languages.
- **Pydantic**: A Python library for data validation using type annotations.
- **BaseModel**: The base class in Pydantic for creating data models.
- **Provider**: In Pulumi, a provider is a plugin that interacts with a cloud service.
