# Comprehensive Konductor IaC Template Repository Refactor and Enhancement Roadmap

## Table of Contents

1. [Introduction](#introduction)
2. [Objectives](#objectives)
3. [Overview of the Current Codebase](#overview-of-the-current-codebase)
4. [Proposed Solution](#proposed-solution)
   - [Part 1: Refactoring AWS Module to Align with Kubernetes Modules](#part-1-refactoring-aws-module-to-align-with-kubernetes-modules)
   - [Part 2: Adjusting Version Handling to Be Exclusive to Kubernetes Modules](#part-2-adjusting-version-handling-to-be-exclusive-to-kubernetes-modules)
   - [Part 3: Improving Configuration Schema and Type System Using Pydantic](#part-3-improving-configuration-schema-and-type-system-using-pydantic)
5. [Detailed Implementation Steps](#detailed-implementation-steps)
   - [Part 1 Steps](#part-1-steps)
   - [Part 2 Steps](#part-2-steps)
   - [Part 3 Steps](#part-3-steps)
6. [Additional Considerations](#additional-considerations)
7. [Conclusion](#conclusion)
8. [Appendix: Understanding Pydantic](#appendix-understanding-pydantic)

---

## Introduction

This document serves as a comprehensive roadmap and educational resource for refactoring and enhancing the Konductor Infrastructure as Code (IaC) codebase. It is designed to guide junior developers through the process of aligning the AWS module with existing Kubernetes modules, adjusting version handling mechanisms, and improving the configuration schema using Pydantic. Each step is thoroughly explained to ensure a deep understanding of the reasoning behind the changes.

---

## Objectives

- **Consistency**: Align the AWS module structure and deployment logic with that of the Kubernetes modules.
- **Modular Version Handling**: Ensure that version locking mechanisms are exclusive to Kubernetes modules.
- **Enhanced Configuration Management**: Implement Pydantic for configuration models to improve type safety and validation.
- **Extensibility**: Prepare the codebase for future support of other cloud providers like GCP and Azure.
- **Educational Resource**: Provide detailed explanations to serve as a learning tool for junior developers.

---

## Overview of the Current Codebase

### Current Situation

- **Kubernetes Modules**:
  - Each module resides under `pulumi/modules/<module_name>/`.
  - Contains `types.py` for configuration, `deploy.py` for deployment logic, and `README.md` for documentation.
  - Deployment functions have a consistent signature and return values.
  - Dynamic module discovery and deployment are handled via `core/deployment.py` and `__main__.py`.

- **AWS Module**:
  - Does not conform to the structure of Kubernetes modules.
  - Has a different code organization and deployment function signature.
  - Integration with the core module and dynamic discovery is inconsistent.
  - Version handling is not aligned with the strategy used for Kubernetes modules.

### Issues Identified

- **Inconsistency**: The AWS module's structure and deployment logic differ from the standard pattern established by the Kubernetes modules.
- **Version Handling**: Version interfaces and locking mechanisms are present in the AWS module but are unnecessary since cloud provider modules rely on SDK versions specified in `requirements.txt`.
- **Configuration Complexity**: The configuration schema lacks flexibility and type safety, making it difficult for module maintainers to define complex configurations.

---

## Proposed Solution

### Part 1: Refactoring AWS Module to Align with Kubernetes Modules

- **Goal**: Restructure the AWS module to match the directory and code structure of Kubernetes modules, ensuring consistency across the codebase.
- **Actions**:
  - Move AWS module files under `pulumi/modules/aws/`.
  - Define configuration data classes in `types.py` without unnecessary version attributes.
  - Update the deployment logic in `deploy.py` to match the standard function signature.
  - Modify `__main__.py` and core modules to include and deploy the AWS module consistently.

### Part 2: Adjusting Version Handling to Be Exclusive to Kubernetes Modules

- **Goal**: Ensure that version locking mechanisms are exclusive to Kubernetes modules and remove unnecessary version interfaces from cloud provider modules like AWS.
- **Actions**:
  - Update `core/config.py` and `core/deployment.py` to handle versioning exclusively for Kubernetes modules.
  - Adjust module discovery functions to accommodate modules with and without versioning.
  - Remove version handling code from cloud provider modules.
  - Optionally, implement a utility to extract versions from `requirements.txt` for logging purposes.

### Part 3: Improving Configuration Schema and Type System Using Pydantic

- **Goal**: Enhance the configuration schema by using Pydantic models for type safety, validation, and flexibility, allowing module maintainers to define complex configurations independently.
- **Actions**:
  - Integrate Pydantic into the project.
  - Each module defines its own Pydantic configuration model in `types.py`.
  - Centralize configuration loading and validation in `core/config.py`.
  - Update deployment functions to use validated configuration objects.
  - Provide clear error reporting and documentation.

---

## Detailed Implementation Steps

### Part 1 Steps

#### Step 1: Restructure the AWS Module Directory

**Action**: Move all AWS module files under `pulumi/modules/aws/` to mirror the structure of Kubernetes modules.

**Reasoning**: This ensures consistency in the codebase, making it easier for developers to navigate and maintain modules.

**Implementation**:

- Create the directory `pulumi/modules/aws/` if it doesn't exist.
- Move existing AWS module files into this directory:
  - `types.py`: Defines configuration data classes.
  - `deploy.py`: Contains deployment logic.
  - `README.md`: Provides module documentation.
- Ensure the directory contains an `__init__.py` file to make it a Python package.

#### Step 2: Define Configuration Data Classes in `types.py`

**Action**: Create a configuration data class `AWSConfig` in `pulumi/modules/aws/types.py` without a `version` attribute.

**Reasoning**: Cloud provider modules do not require version locking in the configuration since their versions are managed via `requirements.txt`.

**Implementation**:

```python
# pulumi/modules/aws/types.py

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AWSConfig(BaseModel):
    enabled: bool = False
    profile: Optional[str] = None
    region: str
    account_id: Optional[str] = None
    landingzones: List[Dict[str, Any]] = []
    # Add other fields as needed

    # Optional: Custom validation methods
    @root_validator
    def check_region(cls, values):
        region = values.get('region')
        if not region:
            raise ValueError('region must be specified for AWS module')
        return values
```

**Explanation**:

- We use Pydantic's `BaseModel` to define the configuration schema.
- The `region` field is required, and a custom validator ensures it is provided.
- The `enabled` field allows the module to be toggled on or off.

#### Step 3: Update Deployment Logic in `deploy.py`

**Action**: Update the AWS module's `deploy.py` to contain a deployment function `deploy_aws_module` with a consistent signature and remove any version handling.

**Reasoning**: Aligning the function signature with other modules ensures consistent deployment patterns and simplifies the core deployment logic.

**Implementation**:

```python
# pulumi/modules/aws/deploy.py

from typing import List, Dict, Any
import pulumi
import pulumi_aws as aws
from .types import AWSConfig

def deploy_aws_module(
        config: AWSConfig,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> pulumi.Resource:
    """
    Deploys the AWS module and returns the primary resource.
    """
    aws_provider = providers.get('aws')
    if not aws_provider:
        raise ValueError("AWS provider not found")

    # Example AWS resource creation
    s3_bucket = aws.s3.Bucket(
        'my_bucket',
        bucket='my-unique-bucket-name',
        opts=pulumi.ResourceOptions(
            provider=aws_provider,
            depends_on=global_depends_on,
        )
    )

    # Return the primary resource
    return s3_bucket
```

**Explanation**:

- The deployment function accepts the validated `config` object, `global_depends_on`, and `providers`.
- It retrieves the AWS provider from the `providers` dictionary.
- An example AWS resource (S3 bucket) is created using the provider.
- The function returns the primary resource without version information.

#### Step 4: Modify `__main__.py` to Include AWS Module

**Action**: Update `pulumi/__main__.py` to include and deploy the AWS module consistently with other modules.

**Reasoning**: This ensures that the AWS module is integrated into the deployment process in the same way as Kubernetes modules.

**Implementation**:

```python
# pulumi/__main__.py

from pulumi import log
from core.config import export_results, get_module_config
from core.deployment import initialize_pulumi, deploy_modules

def main():
    try:
        # Initialize Pulumi
        init = initialize_pulumi()

        # Extract components
        config = init["config"]
        k8s_provider = init["k8s_provider"]
        versions = init["versions"]  # For Kubernetes modules
        configurations = init["configurations"]
        default_versions = init["default_versions"]
        global_depends_on = init["global_depends_on"]
        compliance_config = init.get("compliance_config", {})

        # Initialize AWS provider if AWS module is enabled
        aws_config_obj, aws_enabled = get_module_config('aws', config)
        aws_provider = None
        if aws_enabled:
            from pulumi_aws import Provider as AWSProvider
            aws_provider = AWSProvider(
                'aws_provider',
                profile=aws_config_obj.profile,
                region=aws_config_obj.region,
            )

        # Prepare providers dictionary
        providers = {
            'k8s': k8s_provider,
            'aws': aws_provider,
            # Add other providers as needed
        }

        # Modules to deploy
        modules_to_deploy = [
            "aws",
            # Add other modules as needed
        ]

        # Deploy modules
        deploy_modules(
            modules=modules_to_deploy,
            config=config,
            global_depends_on=global_depends_on,
            providers=providers,
            versions=versions,  # Kubernetes modules will update this
            configurations=configurations,
        )

        # Export stack outputs
        export_results(versions, configurations, compliance_config)

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
```

**Explanation**:

- The AWS module is included in `modules_to_deploy`.
- The AWS provider is initialized if the module is enabled and added to the `providers` dictionary.
- Version handling for the AWS module is omitted, as it is unnecessary.

#### Step 5: Adjust `core/deployment.py` to Handle Providers and Versioning

**Action**: Modify `deploy_module` in `pulumi/core/deployment.py` to handle modules with and without versioning.

**Reasoning**: The core deployment function needs to accommodate both Kubernetes modules (which use versioning) and cloud provider modules (which do not).

**Implementation**:

```python
# pulumi/core/deployment.py

def deploy_module(
    module_name: str,
    config: pulumi.Config,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]]
) -> None:
    # Retrieve module configuration and enabled status
    config_obj, module_enabled = get_module_config(module_name, config)

    if module_enabled:
        # Discover module's deploy function
        deploy_func = discover_deploy_function(module_name)

        # Deploy the module
        result = deploy_func(
            config=config_obj,
            global_depends_on=global_depends_on,
            providers=providers,
        )

        # Handle result based on module type
        if module_name in KUBERNETES_MODULES:
            # Modules with versioning
            version, primary_resource = result
            versions[module_name] = version  # Update versions dictionary
        else:
            # Modules without versioning
            primary_resource = result

        configurations[module_name] = {"enabled": module_enabled}
        global_depends_on.append(primary_resource)

    else:
        log.info(f"Module {module_name} is not enabled.")
```

**Explanation**:

- The function checks if the module is enabled.
- For Kubernetes modules, it expects the deployment function to return a tuple `(version, primary_resource)`.
- For cloud provider modules like AWS, it expects the deployment function to return just the primary resource.
- The `KUBERNETES_MODULES` list defines which modules require version handling.

### Part 2 Steps

#### Step 6: Update `core/config.py` to Handle Versioning Exclusively for Kubernetes Modules

**Action**: Adjust `get_module_config` to include version information only for Kubernetes modules.

**Reasoning**: Cloud provider modules do not need version information in their configuration.

**Implementation**:

```python
# pulumi/core/config.py

KUBERNETES_MODULES = [
    'cert_manager',
    'kubevirt',
    'multus',
    'hostpath_provisioner',
    'containerized_data_importer',
    'prometheus',
    # Add other Kubernetes modules as needed
]

def get_module_config(
        module_name: str,
        config: pulumi.Config,
    ) -> Tuple[Any, bool]:
    module_config_dict = config.get_object(module_name) or {}
    module_enabled = module_config_dict.get('enabled', False)

    # Import the module's configuration class
    types_module = importlib.import_module(f"modules.{module_name}.types")
    ModuleConfigClass = getattr(types_module, f"{module_name.capitalize()}Config")

    if module_name in KUBERNETES_MODULES:
        # Inject version information for Kubernetes modules
        default_versions = load_default_versions()
        module_config_dict['version'] = module_config_dict.get('version', default_versions.get(module_name))

    try:
        # Create an instance of the configuration model
        config_obj = ModuleConfigClass(**module_config_dict)
    except ValidationError as e:
        # Handle validation errors
        pulumi.log.error(f"Configuration error in module '{module_name}':\n{e}")
        raise

    return config_obj, module_enabled
```

**Explanation**:

- The function checks if the module is a Kubernetes module.
- If so, it injects the version information from the default versions.
- This ensures that only Kubernetes modules have version data in their configurations.

#### Step 7: Adjust Module Discovery Functions

**Action**: Ensure `discover_config_class` and `discover_deploy_function` work correctly for all modules.

**Reasoning**: These functions need to dynamically import the appropriate classes and functions for each module, regardless of whether they handle versioning.

**Implementation**:

```python
# pulumi/core/deployment.py

def discover_config_class(module_name: str) -> Type:
    types_module = importlib.import_module(f"modules.{module_name}.types")
    for name, obj in inspect.getmembers(types_module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            return obj
    raise ValueError(f"No Pydantic BaseModel found in modules.{module_name}.types")

def discover_deploy_function(module_name: str) -> Callable:
    deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
    function_name = f"deploy_{module_name}_module"
    deploy_function = getattr(deploy_module, function_name, None)
    if not deploy_function:
        raise ValueError(f"No deploy function named '{function_name}' found in modules.{module_name}.deploy")
    return deploy_function
```

**Explanation**:

- The `discover_config_class` function looks for classes inheriting from `BaseModel`, indicating a Pydantic model.
- The `discover_deploy_function` dynamically imports the deploy function based on the module name.

#### Step 8: Remove Version Handling from Cloud Provider Modules

**Action**: Review cloud provider modules (AWS, GCP, Azure) and remove any version-related code.

**Reasoning**: Since versioning is managed via `requirements.txt` for these modules, internal version handling is unnecessary.

**Implementation**:

- **In `types.py`**:
  - Ensure no `version` field is present in the configuration models.
- **In `deploy.py`**:
  - Ensure deployment functions do not return version information.
  - Remove any logic that deals with versioning.

**Explanation**:

- This simplifies the modules and prevents confusion regarding version handling.

#### Step 9: Optional - Load Versions from `requirements.txt`

**Action**: Implement a utility function to extract module versions from `requirements.txt` for logging or documentation purposes.

**Reasoning**: This provides transparency on the versions of cloud provider SDKs being used.

**Implementation**:

```python
# pulumi/core/utils.py

def get_module_version_from_requirements(module_name: str) -> Optional[str]:
    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                if module_name in line:
                    version = line.strip().split('==')[1]
                    return version
    except Exception as e:
        pulumi.log.warn(f"Error reading requirements.txt: {e}")
    return None
```

**Explanation**:

- The function parses `requirements.txt` to find the version of the specified module.
- This can be used for logging purposes but should not affect module configuration.

### Part 3 Steps

#### Step 10: Integrate Pydantic into the Project

**Action**: Add Pydantic to the project dependencies and update `requirements.txt`.

**Reasoning**: Pydantic provides robust data validation and type safety for configurations.

**Implementation**:

- Install Pydantic:

  ```bash
  pip install pydantic
  ```

- Add to `requirements.txt`:

  ```
  pydantic>=1.8.2
  ```

#### Step 11: Define Base Configuration Classes

**Action**: Create a base configuration class that other modules can inherit from if needed.

**Reasoning**: Provides a common structure and default fields for all modules.

**Implementation**:

```python
# pulumi/core/base_config.py

from pydantic import BaseModel

class BaseConfig(BaseModel):
    enabled: bool = False
```

#### Step 12: Update Module Configuration Models to Use Pydantic

**Action**: For each module, define a Pydantic model in `types.py`.

**Reasoning**: This gives each module autonomy over its configuration schema and ensures type safety.

**Implementation**:

- **For AWS Module**:

  ```python
  # pulumi/modules/aws/types.py

  from pydantic import BaseModel, root_validator
  from typing import Optional, List, Dict, Any

  class AWSConfig(BaseModel):
      enabled: bool = False
      profile: Optional[str] = None
      region: str
      account_id: Optional[str] = None
      landingzones: List[Dict[str, Any]] = []

      @root_validator
      def check_region(cls, values):
          region = values.get('region')
          if not region:
              raise ValueError('region must be specified for AWS module')
          return values
  ```

- **For Kubernetes Module**:

  ```python
  # pulumi/modules/cert_manager/types.py

  from pydantic import BaseModel

  class CertManagerConfig(BaseModel):
      enabled: bool = False
      version: str = "latest"
      namespace: str = "cert-manager"
      install_crds: bool = True
  ```

**Explanation**:

- Each module defines its own configuration model, which can include any fields and validation logic needed.
- This allows for complex and nested configurations as required.

#### Step 13: Centralize Configuration Loading and Validation

**Action**: Update `core/config.py` to load configurations using Pydantic models.

**Reasoning**: Centralizing configuration loading ensures consistency and reduces duplication.

**Implementation**:

```python
# pulumi/core/config.py

from typing import Any, Tuple
from pydantic import ValidationError
import importlib

def get_module_config(
        module_name: str,
        config: pulumi.Config,
    ) -> Tuple[Any, bool]:
    module_config_dict = config.get_object(module_name) or {}
    module_enabled = module_config_dict.get('enabled', False)

    # Import the module's configuration class
    types_module = importlib.import_module(f"modules.{module_name}.types")
    ModuleConfigClass = getattr(types_module, f"{module_name.capitalize()}Config")

    try:
        # Create an instance of the configuration model
        config_obj = ModuleConfigClass(**module_config_dict)
    except ValidationError as e:
        # Handle validation errors
        pulumi.log.error(f"Configuration error in module '{module_name}':\n{e}")
        raise

    return config_obj, module_enabled
```

**Explanation**:

- The function dynamically imports the module's configuration class.
- It creates an instance of the configuration model, which automatically validates the data.
- Any validation errors are caught and reported.

#### Step 14: Update Deployment Functions to Use Validated Configurations

**Action**: Modify deployment functions to accept the validated configuration objects.

**Reasoning**: Ensures that deployment logic operates on valid data, simplifying error handling and code complexity.

**Implementation**:

```python
# pulumi/modules/aws/deploy.py

def deploy_aws_module(
        config: AWSConfig,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> pulumi.Resource:
    aws_provider = providers.get('aws')
    if not aws_provider:
        raise ValueError("AWS provider not found")

    # Use configuration values directly
    region = config.region
    profile = config.profile
    # ...

    # Implement AWS resource creation using aws_provider
    # ...
```

**Explanation**:

- The deployment function uses the validated `config` object, eliminating the need for additional validation within the function.
- Configuration values are accessed directly from the `config` object.

#### Step 15: Provide Clear Error Reporting

**Action**: Ensure that validation errors are clearly reported to the user.

**Reasoning**: Improves user experience by helping users quickly identify and fix configuration issues.

**Implementation**:

- Errors are caught in `get_module_config` and logged with detailed information.
- Example error message:

  ```
  Configuration error in module 'aws':
  1 validation error for AWSConfig
  region
    field required (type=value_error.missing)
  ```

#### Step 16: Document Configuration Schemas

**Action**: Update module `README.md` files to include configuration schemas and field explanations.

**Reasoning**: Provides users with a clear reference for configuring modules, reducing errors and support requests.

**Implementation**:

- **Example for AWS Module**:

  ```markdown
  # AWS Module Configuration

  ## Configuration Schema

  ```yaml
  aws:
    enabled: true
    profile: "default"
    region: "us-west-2"
    account_id: "123456789012"
    landingzones:
      - name: "tenant1"
        email: "tenant1@example.com"
        # Add other fields as needed
  ```

  ## Configuration Fields

  - **enabled** *(bool)*: Enable or disable the AWS module.
  - **profile** *(string)*: AWS CLI profile to use.
  - **region** *(string, required)*: AWS region.
  - **account_id** *(string)*: AWS account ID.
  - **landingzones** *(list)*: List of landing zone configurations.
    - **name** *(string)*: Name of the landing zone.
    - **email** *(string)*: Email associated with the landing zone.
    - *...*
  ```

**Explanation**:

- Users can refer to the documentation to understand how to configure the module.
- This reduces the learning curve and potential configuration errors.

---

## Additional Considerations

### Consistent Function Signatures

Ensure all deployment functions follow the standard signature:

```python
def deploy_<module_name>_module(
        config: <ModuleConfigClass>,
        global_depends_on: List[pulumi.Resource],
        providers: Dict[str, Any],
    ) -> Union[Tuple[str, pulumi.Resource], pulumi.Resource]:
    # Deployment logic
```

- **Kubernetes Modules**: Return a tuple `(version, primary_resource)`.
- **Cloud Provider Modules**: Return the `primary_resource`.

### Code Comments and Docstrings

- Add comments and docstrings to explain complex logic and important implementation details.
- Use standard documentation practices to improve code readability.

### Testing and Validation

- **Unit Tests**: Write tests for configuration models and deployment functions.
- **Integration Tests**: Test module deployment in a controlled environment.
- **Pulumi Preview**: Use `pulumi preview` to validate infrastructure changes before deployment.

---

## Conclusion

By following this comprehensive roadmap, the Konductor IaC codebase will be refactored and enhanced to:

- **Achieve Consistency**: Align module structures and deployment patterns across the codebase.
- **Improve Configuration Management**: Use Pydantic for type-safe and validated configurations.
- **Optimize Version Handling**: Apply version locking exclusively to Kubernetes modules where it is needed.
- **Enhance Developer and User Experience**: Provide clear documentation, error messages, and consistent patterns.
- **Prepare for Future Extensibility**: Facilitate the addition of new modules and support for other cloud providers.

This document serves as both a plan of action and an educational resource for junior developers, providing detailed explanations and reasoning for each step.

---

## Appendix: Understanding Pydantic

To ensure that all developers are comfortable with Pydantic and its usage in the codebase, please refer to the following detailed explainer on Pydantic:

[**Pydantic in Konductor**](#pydantic-in-konductor)

---

### **Pydantic in Konductor**

**Pydantic** is a Python library used for **data validation** and **settings management** using Python type annotations. In the Konductor IaC codebase, Pydantic plays a crucial role in ensuring that module configurations are type-safe, valid, and easy to manage.

#### Why Use Pydantic in Konductor?

- **Type Safety**: Enforces data types, reducing runtime errors due to type mismatches.
- **Data Validation**: Automatically validates configuration data, ensuring it meets the required criteria.
- **Ease of Use**: Integrates seamlessly with Python's type annotations and has a simple syntax.
- **Customization**: Allows for complex nested configurations and custom validation logic.
- **Error Reporting**: Provides clear and informative error messages, improving the developer and user experience.

#### Getting Started with Pydantic

1. **Installation**:

   ```bash
   pip install pydantic
   ```

2. **Defining a Model**:

   ```python
   from pydantic import BaseModel

   class ModuleConfig(BaseModel):
       enabled: bool = False
       name: str
       version: str = "latest"
   ```

3. **Validation and Usage**:

   ```python
   try:
       config = ModuleConfig(**user_input)
   except ValidationError as e:
       print(e)
   ```

#### Advanced Features

- **Nested Models**: Define complex configurations with nested models.
- **Custom Validators**: Implement custom validation logic for specific fields.
- **Settings Management**: Use `BaseSettings` for managing environment variables and configuration files.
