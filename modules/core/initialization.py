# konductor/core/initialization.py
import pulumi
from pulumi import log
from pydantic import BaseSettings
from typing import Any, Dict

from core.types import InitializationConfig
from core.config import load_default_versions
from core.metadata import collect_git_info

def initialize_pulumi() -> InitializationConfig:
    """
    Initializes Pulumi and loads the configuration.

    Returns:
        InitializationConfig: The initialized configuration object.
    """
    try:
        # Load Pulumi configuration
        config = pulumi.Config()

        # Retrieve stack and project names
        stack_name = pulumi.get_stack()
        project_name = pulumi.get_project()

        # Load default module versions
        default_versions = load_default_versions(config)

        # Collect Git information
        git_info = collect_git_info()

        # Create the InitializationConfig object
        init_config = InitializationConfig(
            config=config,
            stack_name=stack_name,
            project_name=project_name,
            default_versions=default_versions,
            git_info=git_info,
            # Other initialization parameters can be added here
        )

        return init_config

    except Exception as e:
        log.error(f"Initialization failed: {str(e)}")
        raise
