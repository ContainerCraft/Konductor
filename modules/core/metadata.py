# ./modules/core/metadata.py

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It provides a thread-safe singleton for consistent metadata management
across all resources in a Pulumi program.
"""

from pydantic import ValidationError
from datetime import datetime, timezone

import pulumi
from pulumi import Config, log

from .types import (
    ComplianceConfig,
    MetadataSingleton,
    GitInfo,
    SourceRepository,
    StackConfig,
    GlobalMetadata,
)


def get_compliance_metadata() -> ComplianceConfig:
    """
    Get compliance metadata from the global singleton.

    Returns:
        ComplianceConfig: Current compliance configuration
    """
    try:
        metadata = MetadataSingleton()
        if compliance_metadata := metadata.get_module_metadata("compliance"):
            try:
                return ComplianceConfig.model_validate(compliance_metadata)
            except ValidationError as e:
                log.error(f"Compliance metadata validation error: {str(e)}")
                return ComplianceConfig.from_pulumi_config(
                    Config(),
                    datetime.now(timezone.utc)
                )
        return ComplianceConfig.create_default()
    except Exception as e:
        log.error(f"Failed to get compliance metadata: {str(e)}")
        return ComplianceConfig.create_default()


def get_git_metadata() -> GitInfo:
    """
    Get git metadata from the global singleton.

    Returns:
        GitInfo: Current git metadata
    """
    try:
        metadata = MetadataSingleton()
        git_data = metadata.git_metadata
        log.debug(f"Retrieved git metadata from singleton: {git_data}")

        # Convert the stored metadata format to GitInfo format
        return GitInfo(
            commit_hash=str(git_data.get('commit', 'unk')),
            branch_name=str(git_data.get('branch', 'unk')),
            remote_url=str(git_data.get('remote', 'unk')),
            release_tag=git_data.get('tag')
        )
    except Exception as e:
        log.error(f"Failed to get git metadata: {str(e)}")
        return GitInfo()


def export_compliance_metadata() -> None:
    """
    Export compliance metadata to Pulumi stack outputs.
    Uses metadata from the global singleton.
    """
    try:
        log.info("Exporting compliance metadata")
        metadata = MetadataSingleton()  # noqa: F841 - Used for side effects

        # Get Git metadata and convert to SourceRepository
        git_info = get_git_metadata()
        log.debug(f"Git info for export: {git_info.model_dump()}")

        source_repo = SourceRepository(
            branch=git_info.branch_name,
            commit=git_info.commit_hash,
            remote=git_info.remote_url,
            tag=git_info.release_tag
        )
        log.debug(f"Created source repo: {source_repo.model_dump()}")

        # Create the stack config structure using the metadata instance
        stack_config = StackConfig(
            compliance=get_compliance_metadata(),
            metadata=GlobalMetadata(),
            source_repository=source_repo
        )

        # Export the stack outputs
        stack_outputs = {
            "stack": stack_config.model_dump(),
        }
        log.debug(f"Exporting stack outputs: {stack_outputs}")
        pulumi.export("stack_outputs", stack_outputs)
        log.info("Successfully exported compliance metadata")

    except Exception as e:
        log.error(f"Failed to export compliance metadata: {str(e)}")
        raise
