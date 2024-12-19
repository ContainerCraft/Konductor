# ./modules/core/initialization.py

"""
Pulumi Initialization Module

This module handles the initialization of Pulumi projects and stacks.
It provides functionality for loading configurations, setting up workspaces,
and initializing the Pulumi runtime environment.
"""

from pulumi import Config, get_stack, get_project, log
from datetime import datetime, timezone

from .types import (
    InitializationConfig,
    ComplianceConfig,
    CommonMetadataFields,
    MetadataSingleton,
)
from .git import collect_git_info


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
        # Create program start timestamp in UTC
        program_start_time = datetime.now(timezone.utc)

        # Load Pulumi configuration
        pulumi_config = Config()

        # Get stack and project names from Pulumi
        stack_name = get_stack()
        project_name = get_project()
        log.info(f"Initializing project: [{project_name}], stack: [{stack_name}]")

        # Get compliance config
        compliance_config = ComplianceConfig.from_pulumi_config(
            pulumi_config,
            program_start_time
        )

        # Store compliance config in singleton
        MetadataSingleton().set_module_metadata(
            "compliance",
            compliance_config.model_dump()
        )

        # Initialize default metadata structure
        metadata = CommonMetadataFields(
            tags={},
            labels={},
            annotations={},
        )

        # Create the initialization config
        init_config = InitializationConfig(
            pulumi_config=pulumi_config,
            stack_name=stack_name,
            project_name=project_name,
            git_info=collect_git_info(),
            metadata=metadata,
            deployment_date_time=program_start_time.isoformat(),
            compliance_config=compliance_config,
            enabled=True,  # Base config is always enabled
        )

        log.info(f"Initialization time: [{program_start_time}]")
        return init_config

    except Exception as e:
        log.error(f"Failed to initialize Pulumi: {str(e)}")
        raise
