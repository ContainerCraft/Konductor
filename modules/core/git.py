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
import semver
from typing import Dict, Optional
from git import Repo, GitCommandError, InvalidGitRepositoryError
from pulumi import log
import subprocess
from .types import GitInfo


def get_latest_semver_tag(repo: Repo) -> Optional[str]:
    """
    Retrieves the latest semantic version tag from a Git repository if the current commit is tagged.

    Args:
        repo: GitPython Repo object

    Returns:
        Optional[str]: Latest semantic version tag or None if current commit is not tagged.
    """
    try:
        # Filter and sort tags that are valid semver
        valid_tags = []
        for tag in repo.tags:
            if hasattr(tag, "name"):
                # Remove 'v' prefix if present for semver parsing
                version_str = tag.name.lstrip("v")
                if semver.Version.parse(version_str, optional_minor_patch=True):
                    valid_tags.append(tag)

        if not valid_tags:
            return None

        # Sort tags by version and return the latest
        sorted_tags = sorted(
            valid_tags,
            key=lambda t: semver.Version.parse(t.name.lstrip("v")),
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
    Retrieves the remote URL of the current Git repository trying via multiple methods.

    Attempt Strategy & Priority:
    1. Use GitPython Repo object
    2. Use git command `git config --get remote.origin.url`
    3. Use `git remote get-url origin`
    4. Use environment variables
    5. Try reading .git/config file directly

    Returns:
        str: Remote URL or 'unknown' if not found
    """
    remote_url = None

    # Method 1: Use GitPython Repo object
    try:
        repo = Repo(os.getcwd(), search_parent_directories=True)
        remote = next(
            (remote for remote in repo.remotes if remote.name == "origin"), None
        )
        if remote:
            remote_url = remote.url
    except (InvalidGitRepositoryError, GitCommandError, StopIteration) as e:
        log.warn(f"GitPython failed to get remote URL: {str(e)}")

    # Method 2: Use git command `git config --get remote.origin.url`
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
            if not remote_url:
                log.warn(
                    "No remote URL found using 'git config --get remote.origin.url'."
                )
                remote_url = None
        except subprocess.CalledProcessError as e:
            log.warn(f"Git command failed to get remote URL: {str(e)}")

    # Method 3: Use `git remote get-url origin`
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
            if not remote_url:
                log.warn("No remote URL found using 'git remote get-url origin'.")
                remote_url = None
        except subprocess.CalledProcessError as e:
            log.warn(
                f"Git command failed to get remote URL using 'git remote get-url origin': {str(e)}"
            )

    # Method 4: Use environment variables
    if not remote_url:
        for env_var in [
            "CI_REPOSITORY_URL",
            "GITHUB_REPOSITORY",
            "GIT_URL",
            "GITHUB_SERVER_URL",
            "GITHUB_REPOSITORY",
        ]:
            url = os.getenv(env_var)
            if url:
                # Handle GitHub specific format
                if env_var == "GITHUB_REPOSITORY":
                    github_server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
                    remote_url = f"{github_server}/{url}.git"
                else:
                    remote_url = url
                break

    # Method 5: Try reading .git/config file directly
    if not remote_url:
        try:
            git_dir = (
                subprocess.check_output(
                    ["git", "rev-parse", "--git-dir"], stderr=subprocess.PIPE
                )
                .decode()
                .strip()
            )
            config_path = os.path.join(git_dir, "config")

            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config_content = f.read()
                    url_match = re.search(r"url\s*=\s*(.+)", config_content)
                    if url_match:
                        remote_url = url_match.group(1).strip()
        except (subprocess.CalledProcessError, IOError) as e:
            log.warn(f"Failed to read .git/config for remote URL: {str(e)}")

    if remote_url and is_valid_git_url(remote_url):
        return remote_url
    else:
        log.warn("Remote URL could not be determined.")
        return "unknown"


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
        log.warn(f"Error extracting repository name from URL: {str(e)}")
        return remote_url


def collect_git_info() -> GitInfo:
    """
    Collects Git repository information using multiple fallback methods.

    Returns:
        GitInfo: An instance containing Git metadata
    """
    git_info = GitInfo(
        commit_hash="unknown",
        branch_name="unknown",
        remote_url="unknown",
    )

    # Get commit hash
    try:
        git_info.commit_hash = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.PIPE
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError as e:
        log.warn(f"Failed to get Git commit hash: {str(e)}")

    # Get branch name
    try:
        git_info.branch_name = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.PIPE
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError as e:
        log.warn(f"Failed to get Git branch name: {str(e)}")

    # Get remote URL
    git_info.remote_url = get_remote_url()

    # Store in global metadata singleton
    from .metadata import MetadataSingleton

    MetadataSingleton().set_git_metadata(git_info.model_dump())

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

    # Check for common git URL patterns
    patterns = [
        r"^git@[a-zA-Z0-9.\-]+:[a-zA-Z0-9/\-]+(\.git)?$",  # SSH format
        r"^https?://[a-zA-Z0-9.\-]+/[a-zA-Z0-9/\-]+(\.git)?$",  # HTTPS format
        r"^https?://[a-zA-Z0-9.\-]+/[a-zA-Z0-9/\-]+$",  # HTTPS without .git
    ]

    return any(re.match(pattern, url) for pattern in patterns)
