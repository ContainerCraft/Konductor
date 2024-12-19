# ./modules/kubernetes/versions.py
"""
Kubernetes module versions.

This module provides the versions for the Kubernetes module.
"""

from typing import Dict
import pulumi




def load_versions_from_file(file_path: Path) -> Dict[str, Any]:
    """
    Loads version information from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dict[str, Any]: Version information dictionary.
    """
    try:
        if file_path.exists():
            with file_path.open("r") as f:
                versions = json.load(f)
                # Validate version formats
                for module, version in versions.items():
                    if version and not validate_version_format(str(version)):
                        log.warn(f"Invalid version format for {module}: {version}")
                log.info(f"Loaded versions from {file_path}")
                return versions
    except (json.JSONDecodeError, OSError) as e:
        log.warn(f"Error loading versions from {file_path}: {str(e)}")
    return {}


def load_default_versions(config: pulumi.Config, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Loads the default versions for modules based on configuration settings.

    This function attempts to load version information from multiple sources:
    1. User-specified source via config
    2. Stack-specific versions file
    3. Local default versions file
    4. Remote versions based on channel

    Args:
        config: The Pulumi configuration object.
        force_refresh: Whether to force refresh the versions cache.

    Returns:
        Dict[str, Any]: Default versions for modules.

    Raises:
        Exception: If versions cannot be loaded from any source.
    """
    ensure_cache_dir()

    if not force_refresh and VERSION_CACHE_FILE.exists():
        if versions := load_versions_from_file(VERSION_CACHE_FILE):
            return versions

    stack_name = pulumi.get_stack()
    default_versions_source = config.get("default_versions.source")
    versions_channel = config.get("versions.channel") or "stable"
    versions_stack_name = coerce_to_bool(config.get("versions.stack_name")) or False

    # Try loading from specified source
    if default_versions_source:
        if default_versions_source.startswith(("http://", "https://")):
            versions = load_versions_from_url(default_versions_source)
        else:
            versions = load_versions_from_file(Path(default_versions_source))

        if versions:
            _cache_versions(versions)
            return versions
        raise Exception(f"Failed to load versions from {default_versions_source}")

    # Try stack-specific versions
    if versions_stack_name:
        stack_versions_path = Path(__file__).parent.parent / "versions" / f"{stack_name}.json"
        if versions := load_versions_from_file(stack_versions_path):
            _cache_versions(versions)
            return versions

    # Try local default versions
    default_versions_path = Path(__file__).parent.parent / "default_versions.json"
    if versions := load_versions_from_file(default_versions_path):
        _cache_versions(versions)
        return versions

    # Try remote versions
    versions_url = f"{DEFAULT_VERSIONS_URL_TEMPLATE}{versions_channel}_versions.json"
    if versions := load_versions_from_url(versions_url):
        _cache_versions(versions)
        return versions

    raise Exception("Cannot proceed without default versions")


def _cache_versions(versions: Dict[str, Any]) -> None:
    """
    Caches version information to file.

    Args:
        versions: Version information to cache.
    """
    try:
        with VERSION_CACHE_FILE.open("w") as f:
            json.dump(versions, f)
    except OSError as e:
        log.warn(f"Failed to cache versions: {str(e)}")


def load_versions_from_url(url: str) -> Dict[str, Any]:
    """
    Loads version information from a URL.

    Args:
        url: URL to fetch versions from.

    Returns:
        Dict[str, Any]: Version information dictionary.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        versions = response.json()
        log.info(f"Loaded versions from {url}")
        return versions
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.warn(f"Error loading versions from {url}: {str(e)}")
    return {}


def validate_version_format(version: str) -> bool:
    """
    Validates semantic version string format.

    Args:
        version: Semver semver string to validate

    Returns:
        bool: True if valid format
    """
    try:
        # Basic semver validation
        parts = version.split(".")
        return len(parts) >= 2 and all(part.isdigit() for part in parts)
    except Exception:
        return False


def validate_url(url: str) -> bool:
    """
    Validates URL format.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid format
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def load_default_versions(config: pulumi.Config) -> Dict[str, str]:
    """
    Loads the default versions for modules.

    Args:
        config: The Pulumi configuration object.

    Returns:
        Dict[str, str]: A dictionary of module names to default versions.
    """
    # Implement logic to load default versions, possibly from a file or remote source
    # For simplicity, return an empty dictionary here
    return {}
