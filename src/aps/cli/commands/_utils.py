"""Shared utilities for CLI commands."""

from pathlib import Path

from aps.core.config_parser import APSConfigParser


def get_tracking_db_path() -> Path:
    """Get the path to the package tracking database."""
    return Path.home() / ".config" / "auto-penguin-setup" / "metadata.jsonl"


def load_category_packages(category: str) -> list[str]:
    """Load packages for a given category from config files."""
    config_dir = Path.home() / ".config" / "auto-penguin-setup"
    parser = APSConfigParser()
    parser.load(config_dir / "packages.ini")

    if not parser.has_section(category):
        raise ValueError(f"Category '{category}' not found in packages.ini")

    return parser.get_section_packages(category)
