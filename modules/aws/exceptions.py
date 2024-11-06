# pulumi/modules/aws/exceptions.py

class AWSModuleError(Exception):
    """Base exception for AWS module errors."""
    pass

class ResourceCreationError(AWSModuleError):
    """Raised when resource creation fails."""
    pass

class ConfigurationError(AWSModuleError):
    """Raised when configuration is invalid."""
    pass

class ComplianceError(AWSModuleError):
    """Raised when compliance requirements are not met."""
    pass

class DeploymentError(AWSModuleError):
    """Deployment execution error."""
    pass
