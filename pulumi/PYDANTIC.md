# **Pydantic in Konductor**

**Pydantic** is a Python library used for **data validation** and **settings management** using Python type annotations. In the Konductor IaC codebase, Pydantic plays a crucial role in ensuring that module configurations are type-safe, valid, and easy to manage.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Why Use Pydantic in Konductor?](#why-use-pydantic-in-konductor)
3. [Getting Started with Pydantic](#getting-started-with-pydantic)
4. [Defining Configuration Models](#defining-configuration-models)
5. [Validation and Error Handling](#validation-and-error-handling)
6. [Advanced Features](#advanced-features)
7. [Practical Example in Konductor](#practical-example-in-konductor)
8. [Best Practices](#best-practices)
9. [Conclusion](#conclusion)

---

## Introduction

In automation and cloud operations, handling configurations and data from various sources is a common task. Ensuring that this data is accurate and correctly structured prevents errors and makes applications more robust. Pydantic leverages Python's type hints to provide data validation and parsing, making it an ideal choice for managing module configurations in Konductor.

---

## Why Use Pydantic in Konductor?

- **Type Safety**: Enforces data types, reducing runtime errors due to type mismatches.
- **Data Validation**: Automatically validates configuration data, ensuring it meets the required criteria.
- **Ease of Use**: Integrates seamlessly with Python's type annotations and has a simple syntax.
- **Customization**: Allows for complex nested configurations and custom validation logic.
- **Error Reporting**: Provides clear and informative error messages, improving the developer and user experience.

---

## Getting Started with Pydantic

### Installation

Ensure Pydantic is included in your project's `requirements.txt`:

```bash
pydantic>=1.8.2
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Defining Configuration Models

Each module in Konductor defines its configuration schema using Pydantic models in `types.py`.

**Example**:

```python
# modules/aws/types.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AWSConfig(BaseModel):
    enabled: bool = False
    profile: Optional[str] = None
    region: str
    account_id: Optional[str] = None
    landingzones: List[Dict[str, Any]] = Field(default_factory=list)
    # ... other fields ...

    @validator('region')
    def validate_region(cls, v):
        if v not in ['us-east-1', 'us-west-2', 'eu-central-1']:
            raise ValueError('Unsupported region specified')
        return v
```

**Explanation**:

- **Fields**: Defined with type annotations and optional default values.
- **Validators**: Custom validation logic to enforce specific rules.

---

## Validation and Error Handling

When configurations are loaded, Pydantic validates the data and raises `ValidationError` if any issues are found.

**Example**:

```python
from pydantic import ValidationError

try:
    config_obj = AWSConfig(**module_config_dict)
except ValidationError as e:
    pulumi.log.error(f"Configuration error in AWS module:\n{e}")
    raise
```

**Error Output**:

```
Configuration error in AWS module:
1 validation error for AWSConfig
region
  Unsupported region specified (type=value_error)
```

---

## Advanced Features

### Nested Models

Modules can define complex configurations using nested models.

```python
# modules/cert_manager/types.py

from pydantic import BaseModel

class IssuerConfig(BaseModel):
    name: str
    email: str

class CertManagerConfig(BaseModel):
    enabled: bool = False
    version: str = "latest"
    namespace: str = "cert-manager"
    issuer: IssuerConfig
```

### Custom Validators

Custom validators can enforce complex validation logic.

```python
from pydantic import validator

class CertManagerConfig(BaseModel):
    # ... fields ...

    @validator('version')
    def check_version_format(cls, v):
        if not v.startswith('v'):
            raise ValueError('Version must start with "v"')
        return v
```

### Environment Variables

Pydantic models can read values from environment variables.

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    aws_region: str

    class Config:
        env_prefix = 'KONDUCTOR_'  # Environment variables start with KONDUCTOR_

settings = Settings()
```

---

## Practical Example in Konductor

**Scenario**: Validate the configuration for the `kubevirt` module.

**Configuration Schema (Pulumi YAML)**:

```yaml
kubevirt:
  enabled: true
  version: "v0.34.0"
  namespace: "kubevirt"
  features:
    liveMigration: true
    cpuManager: false
```

**Configuration Model**:

```python
# modules/kubevirt/types.py

from pydantic import BaseModel

class FeaturesConfig(BaseModel):
    liveMigration: bool = False
    cpuManager: bool = False

class KubeVirtConfig(BaseModel):
    enabled: bool = False
    version: str = "latest"
    namespace: str = "kubevirt"
    features: FeaturesConfig
```

**Usage in Deployment Function**:

```python
def deploy_kubevirt(
    config: KubeVirtConfig,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
) -> pulumi.Resource:
    # Access configuration values directly
    version = config.version
    namespace = config.namespace
    live_migration_enabled = config.features.liveMigration
    # Deployment logic...
```

---

## Best Practices

1. **Define Clear Schemas**: Use Pydantic models to define clear and explicit configuration schemas.
2. **Provide Defaults**: Set default values for optional fields to simplify user configurations.
3. **Validate Early**: Perform validation as soon as configurations are loaded to catch errors early.
4. **Use Custom Validators**: Implement custom validators for complex validation rules.
5. **Document Configurations**: Clearly document all configuration fields and their expected values in module `README.md` files.
6. **Handle Errors Gracefully**: Provide informative error messages to assist users in correcting configuration issues.

---

## Conclusion

Integrating Pydantic into the Konductor IaC codebase enhances both developer and user experiences by providing robust configuration management. It ensures configurations are validated and type-safe, reducing runtime errors and simplifying debugging. By following the best practices outlined in this document, developers can create modules that are reliable, maintainable, and user-friendly.

---

For further reading and advanced usage of Pydantic, refer to the [official Pydantic documentation](https://pydantic-docs.helpmanual.io/).
