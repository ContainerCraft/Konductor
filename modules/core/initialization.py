# ../konductor/modules/core/initialization.py

"""
Pulumi Initialization Module

This module handles the initialization of Pulumi projects and stacks.
It provides functionality for loading configurations, setting up workspaces,
and initializing the Pulumi runtime environment.
"""

import pulumi
from pulumi import Config, get_stack, get_project, log

from modules.core.types import InitializationConfig, GitInfo
from modules.core.git import collect_git_info

def initialize_pulumi() -> InitializationConfig:
    """
    Initializes Pulumi and loads the configuration.

    This function performs the following:
    1. Loads Pulumi configuration
    2. Gets stack and project information
    3. Collects Git metadata
    4. Sets up initial metadata structure

    Returns:
        InitializationConfig: The initialization configuration object.

    Raises:
        Exception: If initialization fails
    """
    try:
        # Load Pulumi configuration
        pulumi_config = Config()

        # Get stack and project names from Pulumi
        stack_name = get_stack()
        project_name = get_project()
        log.info(f"Initializing Pulumi project: {project_name}, stack: {stack_name}")

        # Initialize default metadata structure
        metadata = {
            "labels": {},
            "annotations": {}
        }

        # Create the initialization config
        init_config = InitializationConfig(
            pulumi_config=pulumi_config,
            stack_name=stack_name,
            project_name=project_name,
            default_versions={},
            git_info=collect_git_info(),
            metadata=metadata
        )

        log.info(f"Pulumi initialization completed successfully")
        return init_config

    except Exception as e:
        log.error(f"Failed to initialize Pulumi: {str(e)}")
        raise
