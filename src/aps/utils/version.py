"""Version detection utility for auto-penguin-setup."""

import importlib.metadata
from pathlib import Path


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
        return _get_version_from_pyproject()


def _get_version_from_pyproject() -> str:
    """Fallback to read version from pyproject.toml in development mode.

    Returns:
        str: Version string from pyproject.toml or "dev" if not found

    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if not pyproject_path.exists():
            return "dev"

        with pyproject_path.open() as f:
            for line in f:
                if line.strip().startswith("version"):
                    version = line.split("=")[1].strip().strip('"')
                    return version

        return "dev"
    except (OSError, ValueError, IndexError):
        return "dev"
