"""Path utilities for resolving package-relative directories and files."""

from pathlib import Path


def get_package_root() -> Path:
    """Get the root directory of the APS package.

    This works in both development (src/aps/) and installed modes.

    Returns:
        Path to the package root directory

    """
    # This module is in src/aps/utils/paths.py
    # Navigate up: utils/ -> aps/ -> src/ -> project_root/
    return Path(__file__).parent.parent.parent.parent


def get_configs_dir() -> Path:
    """Get the directory containing system configuration files.

    Returns:
        Path to src/aps/configs/

    """
    # This module is in src/aps/utils/paths.py
    # Navigate: utils/ -> aps/ -> configs/
    return Path(__file__).parent.parent / "configs"


def get_default_configs_dir() -> Path:
    """Get the directory containing default user configuration templates.

    Returns:
        Path to src/aps/configs/default_aps_configs/

    """
    return get_configs_dir() / "default_aps_configs"


def resolve_config_file(filename: str) -> Path:
    """Resolve a system config file path relative to the configs directory.

    Args:
        filename: Relative path from configs/ directory (e.g., "borg/backup.sh")

    Returns:
        Absolute path to the config file

    """
    return get_configs_dir() / filename


def resolve_default_config_file(filename: str) -> Path:
    """Resolve a default config template file path.

    Args:
        filename: Config filename (e.g., "packages.ini")

    Returns:
        Absolute path to the default config file

    """
    return get_default_configs_dir() / filename
