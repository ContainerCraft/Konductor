# modules/core/exceptions.py


class KonductorError(Exception):
    """Base exception class for Konductor platform."""

    pass


class ModuleLoadError(KonductorError):
    """Exception raised when a module cannot be loaded."""


class ModuleDeploymentError(KonductorError):
    """Exception raised when a module deployment fails."""
