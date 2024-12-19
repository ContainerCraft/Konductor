# ./modules/core/git.py

"""
Git Utilities Module

This module provides utility functions for interacting with Git repositories.
It includes functions for retrieving repository information and sanitizing data.

Key Functions:
- get_latest_semver_tag: Retrieves the latest semantic version tag.
- get_remote_url: Retrieves the remote URL of a Git repository.
- sanitize_git_info: Sanitizes Git information for use in tags/labels.
- extract_repo_name: Extracts the repository name from a Git remote URL.
- collect_git_info: Collects Git repository metadata.
- is_valid_git_url: Validates Git URLs.
"""

import os
import re
import semver  # type: ignore # missing stubs
from typing import Dict, Optional
from git import Repo, GitCommandError, InvalidGitRepositoryError  # type: ignore
from pulumi import log
import subprocess

from .types import (
    GitInfo,
    MetadataSingleton,
)


def get_latest_semver_tag(repo: Repo) -> Optional[str]:
    """
    Retrieves the latest semantic version tag from a Git repository.

    Args:
        repo: GitPython Repo object

    Returns:
        Optional[str]: Latest semantic version tag or None if not tagged
    """
    try:
        valid_tags = []
        for tag in repo.tags:
            if hasattr(tag, "name"):
                version_str = tag.name.lstrip("v")
                try:
                    if semver.VersionInfo.parse(version_str):  # type: ignore
                        valid_tags.append(tag)
                except ValueError:
                    continue

        if not valid_tags:
            return None

        sorted_tags = sorted(
            valid_tags,
            key=lambda t: semver.VersionInfo.parse(t.name.lstrip("v")),  # type: ignore
            reverse=True,
        )
        return sorted_tags[0].name if sorted_tags else None

    except GitCommandError as e:
        log.warn(f"Failed to retrieve tags: {str(e)}")
        return None
    except Exception as e:
        log.warn(f"Error processing tags: {str(e)}")
        return None


def get_remote_url() -> str:
    """
    Retrieves the remote URL of the current Git repository.

    Returns:
        str: Remote URL or 'unknown' if not found
    """
    remote_url = None

    # Log working directory
    cwd = os.getcwd()
    log.debug(f"Getting remote URL from directory: {cwd}")

    # Method 1: Use GitPython Repo object
    try:
        repo = Repo(cwd, search_parent_directories=True)
        log.debug(f"Found git repo at: {repo.working_dir}")
        if remote := next(
            (remote for remote in repo.remotes if remote.name == "origin"),
            None
        ):
            remote_url = remote.url
            log.debug(f"Found remote URL via GitPython: {remote_url}")
    except (InvalidGitRepositoryError, GitCommandError) as e:
        log.warn(f"GitPython failed to get remote URL: {str(e)}")

    # Method 2: Git config command
    if not remote_url:
        try:
            remote_url = (
                subprocess.check_output(
                    ["git", "config", "--get", "remote.origin.url"],
                    stderr=subprocess.PIPE,
                )
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError as e:
            log.warn(f"Git config command failed: {str(e)}")

    # Method 3: Git remote command
    if not remote_url:
        try:
            remote_url = (
                subprocess.check_output(
                    ["git", "remote", "get-url", "origin"],
                    stderr=subprocess.PIPE,
                )
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError as e:
            log.warn(f"Git remote command failed: {str(e)}")

    # Method 4: Environment variables
    if not remote_url:
        for env_var in [
            "CI_REPOSITORY_URL",
            "GITHUB_REPOSITORY",
            "GIT_URL",
            "GITHUB_SERVER_URL",
            "GITHUB_REPOSITORY",
        ]:
            if url := os.getenv(env_var):
                if env_var == "GITHUB_REPOSITORY":
                    github_server = os.getenv(
                        "GITHUB_SERVER_URL",
                        "https://github.com"
                    )
                    remote_url = f"{github_server}/{url}.git"
                else:
                    remote_url = url
                break

    # Method 5: Git config file
    if not remote_url:
        try:
            git_dir = (
                subprocess.check_output(
                    ["git", "rev-parse", "--git-dir"],
                    stderr=subprocess.PIPE,
                )
                .decode()
                .strip()
            )
            config_path = os.path.join(git_dir, "config")

            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    if url_match := re.search(r"url\s*=\s*(.+)", f.read()):
                        remote_url = url_match[1].strip()
        except (subprocess.CalledProcessError, IOError) as e:
            log.warn(f"Failed to read git config: {str(e)}")

    if remote_url and is_valid_git_url(remote_url):
        return remote_url

    log.warn("Remote URL could not be determined")
    return "unknown"


def sanitize_git_info(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitizes git information for use in resource tags/labels.

    Args:
        git_info: Raw git information dictionary

    Returns:
        Dict[str, str]: Sanitized git information
    """
    sanitized = {}
    for key, value in git_info.items():
        sanitized_value = re.sub(r"[^a-z0-9-._]", "-", str(value).lower())
        sanitized_value = sanitized_value[:63]
        sanitized_value = re.sub(
            r"^[^a-z0-9]+|[^a-z0-9]+$",
            "",
            sanitized_value
        )
        sanitized[key] = sanitized_value
    return sanitized


def extract_repo_name(remote_url: str) -> str:
    """
    Extracts the repository name from a Git remote URL.

    Args:
        remote_url: The Git remote URL

    Returns:
        str: Repository name or original URL if parsing fails
    """
    try:
        if remote_url.startswith("git@"):
            parts = remote_url.split(":")
            if len(parts) == 2:
                return parts[1].rstrip(".git")

        if match := re.search(r"[:/]([^/:]+/[^/\.]+)(\.git)?$", remote_url):
            return match[1]

        return remote_url
    except Exception as e:
        log.warn(f"Error extracting repository name: {str(e)}")
        return remote_url


def collect_git_info() -> GitInfo:
    """
    Collects Git repository information.

    Returns:
        GitInfo: Git metadata instance
    """
    git_info = GitInfo(
        commit_hash="unknown",
        branch_name="unknown",
        remote_url="unknown",
    )

    try:
        # Get commit hash
        commit_output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.PIPE,
        ).decode().strip()
        git_info.commit_hash = commit_output
        log.debug(f"Got commit hash: {commit_output}")

    except subprocess.CalledProcessError as e:
        log.warn(f"Failed to get commit hash: {str(e)}")

    try:
        # Get branch name
        branch_output = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.PIPE,
        ).decode().strip()
        git_info.branch_name = branch_output
        log.debug(f"Got branch name: {branch_output}")

    except subprocess.CalledProcessError as e:
        log.warn(f"Failed to get branch name: {str(e)}")

    # Get remote URL with debug logging
    remote_url = get_remote_url()
    log.debug(f"Got remote URL: {remote_url}")
    git_info.remote_url = remote_url

    # Try to get release tag
    try:
        repo = Repo(os.getcwd(), search_parent_directories=True)
        tag = get_latest_semver_tag(repo)
        git_info.release_tag = tag
        log.debug(f"Got release tag: {tag}")
    except Exception as e:
        log.warn(f"Failed to get release tag: {str(e)}")

    # Store in metadata singleton and log the data
    metadata_dict = git_info.model_dump()
    log.debug(f"Storing git metadata: {metadata_dict}")
    MetadataSingleton().set_git_metadata(metadata_dict)

    return git_info


def is_valid_git_url(url: str) -> bool:
    """
    Validates if a string is a valid git URL.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid git URL
    """
    if not url or url == "unknown":
        return False

    patterns = [
        r"^git@[a-zA-Z0-9.\-]+:[a-zA-Z0-9/\-]+(\.git)?$",  # SSH
        r"^https?://[a-zA-Z0-9.\-]+/[a-zA-Z0-9/\-]+(\.git)?$",  # HTTPS
        r"^https?://[a-zA-Z0-9.\-]+/[a-zA-Z0-9/\-]+$",  # HTTPS no .git
    ]

    return any(re.match(pattern, url) for pattern in patterns)
