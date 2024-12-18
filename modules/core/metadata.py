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

from .types import ComplianceConfig
from .types.base import MetadataSingleton


def get_compliance_metadata() -> ComplianceConfig:
    """
    Get compliance metadata from the global singleton.
    """
    try:
        metadata = MetadataSingleton()
        if compliance_metadata := metadata.get_module_metadata("compliance"):
            try:
                return ComplianceConfig.model_validate(compliance_metadata)
            except ValidationError as e:
                log.error(f"Compliance metadata validation error: {str(e)}")
                # Try parsing with more lenient validation
                return ComplianceConfig.from_pulumi_config(Config(), datetime.now(timezone.utc))
        return ComplianceConfig()
    except Exception as e:
        log.error(f"Failed to get compliance metadata: {str(e)}")
        return ComplianceConfig()


def export_compliance_metadata() -> None:
    """
    Export compliance metadata to Pulumi stack outputs.
    Uses metadata from the global singleton.
    """
    try:
        log.info("Exporting compliance metadata")
        metadata_singleton = MetadataSingleton()

        # Get compliance metadata
        compliance_metadata = get_compliance_metadata()

        # Get Git metadata
        git_metadata = metadata_singleton.git_metadata
        git_info = {
            "branch": git_metadata.get("branch_name", "unknown"),
            "commit": git_metadata.get("commit_hash", "unknown"),
            "remote": git_metadata.get("remote_url", "unknown"),
        }

        # Create the compliance export structure
        stack_outputs = {
            "config": {
                "compliance": compliance_metadata.model_dump(),
                "source_repository": git_info,
            }
        }

        # Export the stack outputs
        pulumi.export("stack_outputs", stack_outputs)
        log.info("Successfully exported compliance metadata")

    except Exception as e:
        log.error(f"Failed to export compliance metadata: {str(e)}")
        raise
