"""
Git Utilities Module

This module provides utility functions for interacting with Git repositories.
It includes functions for retrieving repository information, and sanitizing data.

Key Functions:
- get_latest_semver_tag: Retrieves the latest semantic version tag.
- get_remote_url: Retrieves the remote URL of a Git repository.
- sanitize_git_info: Sanitizes Git information for use in tags/labels.
- extract_repo_name: Extracts the repository name from a Git remote URL.
"""

import os
import re
import semver
from typing import Dict, Optional, Any
from git import Repo, GitCommandError
from pulumi import log
import subprocess
from modules.core.types import GitInfo

def get_latest_semver_tag(repo: Repo) -> Optional[str]:
    """
    Retrieves the latest semantic version tag from a Git repository.

    Args:
        repo: GitPython Repo object

    Returns:
        Optional[str]: Latest semantic version tag or None if no valid tags found.
    """
    try:
        tags = sorted(
            (tag for tag in repo.tags if semver.VersionInfo.isvalid(tag.name)),
            key=lambda t: semver.VersionInfo.parse(t.name),
            reverse=True
        )
        return tags[0].name if tags else None
    except GitCommandError as e:
        log.warn(f"Failed to retrieve tags: {str(e)}")
        return None

def get_remote_url(repo: Repo) -> str:
    """
    Retrieves the remote URL of a Git repository.

    Args:
        repo: GitPython Repo object

    Returns:
        str: Remote URL or 'N/A' if not found
    """
    try:
        return next(remote.url for remote in repo.remotes if remote.name == "origin")
    except (StopIteration, AttributeError, GitCommandError) as e:
        log.warn(f"Failed to get remote URL: {str(e)}")
        pass

    try:
        return repo.git.config("--get", "remote.origin.url")
    except GitCommandError:
        pass

    for env_var in ["CI_REPOSITORY_URL", "GITHUB_REPOSITORY", "GIT_URL"]:
        if url := os.getenv(env_var):
            return url

    return "N/A"

def sanitize_git_info(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitizes git information for use in resource tags/labels.
    Ensures values meet length and character requirements.

    Args:
        git_info: Raw git information dictionary

    Returns:
        Dict[str, str]: Sanitized git information
    """
    sanitized = {}

    for key, value in git_info.items():
        sanitized_value = re.sub(r"[^a-z0-9-._]", "-", str(value).lower())
        sanitized_value = sanitized_value[:63]
        sanitized_value = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", sanitized_value)
        sanitized[key] = sanitized_value

    return sanitized

def extract_repo_name(remote_url: str) -> str:
    """
    Extracts the repository name from a Git remote URL.
    Handles various Git URL formats.

    Args:
        remote_url: The Git remote URL

    Returns:
        str: The repository name or original URL if parsing fails
    """
    try:
        # Handle SSH URLs
        if remote_url.startswith("git@"):
            parts = remote_url.split(":")
            if len(parts) == 2:
                return parts[1].rstrip(".git")

        # Handle HTTPS URLs
        match = re.search(r"[:/]([^/:]+/[^/\.]+)(\.git)?$", remote_url)
        if match:
            return match.group(1)

        return remote_url
    except Exception as e:
        log.warning(f"Error extracting repo name from {remote_url}: {str(e)}")
        return remote_url

def collect_git_info() -> GitInfo:
    """
    Collects Git repository information.

    Returns:
        GitInfo: An instance containing Git metadata.
    """
    git_info = GitInfo()

    try:
        # Get the latest commit hash
        git_info.commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    except Exception as e:
        log.warning(f"Failed to get commit hash: {str(e)}")

    try:
        # Get the current branch name
        git_info.branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
    except Exception as e:
        log.warning(f"Failed to get branch name: {str(e)}")

    try:
        # Get the remote URL
        git_info.remote_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode().strip()
    except Exception as e:
        log.warning(f"Failed to get remote URL: {str(e)}")

    return git_info
