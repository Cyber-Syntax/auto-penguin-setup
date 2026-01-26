"""Shared utilities for CLI commands."""

import importlib.metadata
from pathlib import Path

from aps.core.config import APSConfigParser, ensure_config_files


def get_tracking_db_path() -> Path:
    """Get the path to the package tracking database."""
    return Path.home() / ".config" / "auto-penguin-setup" / "metadata.jsonl"


def load_category_packages(category: str) -> list[str]:
    """Load packages for a given category from config files."""
    config_dir = Path.home() / ".config" / "auto-penguin-setup"

    # Ensure config files exist, creating them from examples if needed
    ensure_config_files(config_dir)

    parser = APSConfigParser()
    parser.load(config_dir / "packages.ini")

    if not parser.has_section(category):
        raise ValueError(f"Category '{category}' not found in packages.ini")

    return parser.get_section_packages(category)


def get_version() -> str:
    """Get the version of auto-penguin-setup.

    Returns version from package metadata if installed,
    otherwise reads from pyproject.toml (development mode).

    Returns:
        str: Version string (e.g., "0.2.0-alpha" or "dev")

    """
    try:
        return importlib.metadata.version("auto-penguin-setup")
    except importlib.metadata.PackageNotFoundError:
        # This happens if the package isn't installed (e.g., running raw scripts)
        return "dev"
