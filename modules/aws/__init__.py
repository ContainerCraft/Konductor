# ./modules/aws/__init__.py
"""AWS module for Konductor."""

from .types import AWSConfig
from .deployment import AwsModule

__all__ = ["AWSConfig", "AwsModule"]


def deploy(init_config, module_config):
    """For backwards compatibility"""
    from .deployment import AwsModule

    module = AwsModule()
    return module.deploy(module_config, init_config)
