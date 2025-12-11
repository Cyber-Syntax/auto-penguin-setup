"""Configuration file parser for INI files with special APS formats."""

import shutil
from configparser import ConfigParser
from pathlib import Path

from aps.utils.paths import get_default_configs_dir


class APSConfigParser:
    """
    Parser for Auto Penguin Setup INI configuration files.

    Extends standard ConfigParser to handle special formats:
    - Package lists with comma-separated values
    - Package mappings: generic_name=distro:specific_name
    - Prefix handling: COPR:user/repo:package, AUR:package, PPA:user/repo:package
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize parser with optional config file.

        Args:
            config_path: Path to INI configuration file
        """
        self._parser = ConfigParser()
        self._path = config_path

        if config_path and config_path.exists():
            processed_content = self._preprocess_config_file(config_path)
            self._parser.read_string(processed_content)

    def load(self, config_path: Path) -> None:
        """
        Load configuration from file.

        Args:
            config_path: Path to INI configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        self._path = config_path
        processed_content = self._preprocess_config_file(config_path)
        self._parser.read_string(processed_content)

    def _preprocess_config_file(self, config_path: Path) -> str:
        """
        Preprocess config file to convert bare lines to key=value format.

        Bare lines (lines without '=') are converted to numbered keys.
        This allows ConfigParser to read them while maintaining compatibility.

        Args:
            config_path: Path to config file

        Returns:
            Processed content as string
        """
        lines = config_path.read_text(encoding="utf-8").splitlines()
        processed_lines = []
        current_section = None
        key_counter: dict[str, int] = {}

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith(("#", ";")):
                processed_lines.append(line)
                continue

            # Section header
            if stripped.startswith("[") and stripped.endswith("]"):
                current_section = stripped[1:-1]
                key_counter[current_section] = 0
                processed_lines.append(line)
                continue

            # Key-value pair - keep as is
            if "=" in stripped:
                processed_lines.append(line)
                continue

            # Bare line in section - convert to numbered key=value
            if current_section and stripped:
                key = f"_pkg_{key_counter[current_section]}"
                processed_lines.append(f"{key}={stripped}")
                key_counter[current_section] += 1
                continue

            # Unrecognized line - keep as is
            processed_lines.append(line)

        return "\n".join(processed_lines)

    def has_section(self, section: str) -> bool:
        """Check if section exists in configuration."""
        return self._parser.has_section(section)

    def sections(self) -> list[str]:
        """Get list of all sections in configuration."""
        return self._parser.sections()

    def get_section_packages(self, section: str) -> list[str]:
        """
        Get list of packages from a section.

        Supports multiple formats:
        - Comma-separated values: curl, wget, git
        - One package per line
        - Mixed format with inline comments
        - Whitespace tolerance

        Example:
            [core]
            curl, wget  # download tools
            # firewall
            ufw
            trash-cli, syncthing
            borgbackup

        Args:
            section: Section name to read packages from

        Returns:
            List of package names
        """
        if not self._parser.has_section(section):
            return []

        packages: list[str] = []

        # Get all items from section
        for _, value in self._parser.items(section):
            # Split by comma first
            parts = value.split(",")

            for part in parts:
                # Remove inline comments
                if "#" in part:
                    part = part.split("#")[0]
                if ";" in part:
                    part = part.split(";")[0]

                # Strip whitespace and filter out empty strings
                cleaned = part.strip()
                if cleaned:
                    packages.append(cleaned)

        return packages

    def get_package_mappings(self, section: str) -> dict[str, str]:
        """
        Get package name mappings from a section.

        Handles format like:
        [fedora]
        generic_package=fedora_specific_package
        another_pkg=COPR:user/repo:package_name

        Args:
            section: Section name to read mappings from

        Returns:
            Dictionary mapping generic names to distro-specific names
        """
        if not self._parser.has_section(section):
            return {}

        mappings: dict[str, str] = {}
        for key, value in self._parser.items(section):
            mappings[key.strip()] = value.strip()

        return mappings

    def get_variables(self, section: str = "variables") -> dict[str, str]:
        """
        Get variable definitions from configuration.

        Handles format like:
        [variables]
        python_version=3.12
        install_path=/opt/myapp

        Args:
            section: Section name for variables (default: 'variables')

        Returns:
            Dictionary of variable name to value mappings
        """
        if not self._parser.has_section(section):
            return {}

        variables: dict[str, str] = {}
        for key, value in self._parser.items(section):
            variables[key.strip()] = value.strip()

        return variables

    def get(self, section: str, option: str, fallback: str | None = None) -> str | None:
        """
        Get a single configuration value.

        Args:
            section: Section name
            option: Option name within section
            fallback: Default value if option doesn't exist

        Returns:
            Configuration value or fallback
        """
        if fallback is not None:
            return self._parser.get(section, option, fallback=fallback)

        if not self._parser.has_option(section, option):
            return None

        return self._parser.get(section, option)

    def get_all_items(self, section: str) -> dict[str, str]:
        """
        Get all key-value pairs from a section.

        Args:
            section: Section name

        Returns:
            Dictionary of all items in section
        """
        if not self._parser.has_section(section):
            return {}

        return dict(self._parser.items(section))

    @property
    def path(self) -> Path | None:
        """Get the path to the loaded configuration file."""
        return self._path


def parse_config(config_path: Path) -> APSConfigParser:
    """
    Convenience function to create and load a config parser.

    Args:
        config_path: Path to INI configuration file

    Returns:
        Loaded APSConfigParser instance

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    parser = APSConfigParser()
    parser.load(config_path)
    return parser


def ensure_config_files(config_dir: Path | None = None) -> dict[str, bool]:
    """
    Ensure configuration files exist, creating them from examples if needed.

    Args:
        config_dir: Directory for config files (default: ~/.config/auto-penguin-setup)

    Returns:
        Dictionary mapping filename to whether it was created (True) or already existed (False)
    """
    if config_dir is None:
        config_dir = Path.home() / ".config" / "auto-penguin-setup"

    # Get the source examples directory
    examples_dir = get_default_configs_dir()

    if not examples_dir.exists():
        raise FileNotFoundError(f"Config examples directory not found: {examples_dir}")

    # Ensure config directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    # Track which files were created
    results: dict[str, bool] = {}

    # Copy example config files if they don't exist
    config_files = ["packages.ini", "pkgmap.ini", "variables.ini"]

    for filename in config_files:
        source = examples_dir / filename
        destination = config_dir / filename

        if not destination.exists():
            if source.exists():
                shutil.copy2(source, destination)
                results[filename] = True
            else:
                raise FileNotFoundError(f"Example config file not found: {source}")
        else:
            results[filename] = False

    return results
