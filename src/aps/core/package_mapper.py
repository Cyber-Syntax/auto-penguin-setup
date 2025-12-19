"""Package name mapping with support for COPR, AUR, and PPA prefixes."""

import re
from dataclasses import dataclass
from pathlib import Path

from aps.core.config import APSConfigParser
from aps.core.distro import DistroFamily, DistroInfo

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class PackageMapping:
    """Represents a package mapping with source information."""

    original_name: str
    mapped_name: str
    source: str  # "official", "COPR:user/repo", "AUR:pkg", "PPA:user/repo",
    # "flatpak:remote"
    category: str | None = None

    @property
    def is_official(self) -> bool:
        """Check if package is from official repositories."""
        return self.source == "official"

    @property
    def is_copr(self) -> bool:
        """Check if package is from COPR (Fedora)."""
        return self.source.startswith("COPR:")

    @property
    def is_aur(self) -> bool:
        """Check if package is from AUR (Arch)."""
        return self.source.startswith("AUR:")

    @property
    def is_flatpak(self) -> bool:
        """Check if package is from Flatpak."""
        return self.source.startswith("flatpak:")

    def get_repo_name(self) -> str | None:
        """Extract repository name from source prefix.

        Returns:
            Repository name (e.g., "user/repo" for COPR) or None

        """
        if self.is_copr:
            # Format: COPR:user/repo
            match = re.match(r"^COPR:([^:]+)", self.source)
            return match.group(1) if match else None

        if self.is_flatpak:
            # Format: flatpak:remote_name
            match = re.match(r"^flatpak:(.+)", self.source)
            return match.group(1) if match else None
        return None


class PackageMapper:
    """Maps generic package names to distribution-specific names.

    Handles prefix formats:
    - COPR:user/repo:package (Fedora)
    - AUR:package (Arch)
    - flatpak:remote:package (Flatpak)
    """

    def __init__(self, pkgmap_path: Path, distro: DistroInfo) -> None:
        """Initialize package mapper with configuration and distro info.

        Args:
            pkgmap_path: Path to pkgmap.ini configuration file
            distro: Distribution information from distro detection

        """
        self.distro = distro
        self.mappings: dict[str, PackageMapping] = {}
        self._load_mappings(pkgmap_path)

    def _load_mappings(self, pkgmap_path: Path) -> None:
        """Load package mappings from pkgmap.ini configuration.

        Args:
            pkgmap_path: Path to pkgmap.ini file

        """
        logger.debug("Loading mappings from %s", pkgmap_path)
        if not pkgmap_path.exists():
            logger.debug("pkgmap.ini not found at %s", pkgmap_path)
            return

        parser = APSConfigParser(pkgmap_path)

        # Determine section name based on distro family
        section_map = {
            DistroFamily.FEDORA: "pkgmap.fedora",
            DistroFamily.ARCH: "pkgmap.arch",
        }

        section = section_map.get(self.distro.family)
        logger.debug("Looking for section %s", section)
        if not section or not parser.has_section(section):
            logger.debug("Section %s not found in %s", section, pkgmap_path)
            return

        # Load mappings for current distro
        raw_mappings = parser.get_package_mappings(section)
        logger.debug("Raw mappings: %s", raw_mappings)
        for original_name, mapped_value in raw_mappings.items():
            mapping = self._parse_mapping(original_name, mapped_value)
            self.mappings[original_name] = mapping
        logger.debug("Loaded %d mappings", len(self.mappings))

    def _parse_mapping(
        self, original_name: str, mapped_value: str
    ) -> PackageMapping:
        """Parse a mapping value to extract source prefix and package name.

        Supported formats:
        - package_name (official repo)
        - COPR:user/repo:package_name
        - AUR:package_name
        - flatpak:remote:package_name

        Args:
            original_name: Generic package name
            mapped_value: Distro-specific mapping value

        Returns:
            PackageMapping with extracted information

        """
        # Check for COPR format: COPR:user/repo or COPR:user/repo:package
        copr_match = re.match(r"^COPR:([^:]+)(?::(.+))?$", mapped_value)
        if copr_match:
            repo, package = copr_match.groups()
            # If no explicit package name, use original_name
            package_name = package if package else original_name
            return PackageMapping(
                original_name=original_name,
                mapped_name=package_name,
                source=f"COPR:{repo}",
            )

        # Check for AUR format: AUR:package
        aur_match = re.match(r"^AUR:(.+)$", mapped_value)
        if aur_match:
            package = aur_match.group(1)
            return PackageMapping(
                original_name=original_name,
                mapped_name=package,
                source=f"AUR:{package}",
            )

        # Check for Flatpak format: flatpak:remote:package
        flatpak_match = re.match(r"^flatpak:([^:]+):(.+)$", mapped_value)
        if flatpak_match:
            remote, package = flatpak_match.groups()
            return PackageMapping(
                original_name=original_name,
                mapped_name=package,
                source=f"flatpak:{remote}",
            )

        # Default: official repository
        return PackageMapping(
            original_name=original_name,
            mapped_name=mapped_value,
            source="official",
        )

    def map_package(
        self, package_name: str, category: str | None = None
    ) -> PackageMapping:
        """Map package name to distro-specific name and source.

        Args:
            package_name: Generic package name to map
            category: Optional category for tracking

        Returns:
            PackageMapping with distro-specific information

        """
        # Check if we have a mapping for this package
        if package_name in self.mappings:
            mapping = self.mappings[package_name]
            # Update category if provided
            if category:
                return PackageMapping(
                    original_name=mapping.original_name,
                    mapped_name=mapping.mapped_name,
                    source=mapping.source,
                    category=category,
                )
            return mapping

        # No mapping found - assume official repository
        return PackageMapping(
            original_name=package_name,
            mapped_name=package_name,
            source="official",
            category=category,
        )

    def get_packages_by_source(
        self, source_prefix: str
    ) -> list[PackageMapping]:
        """Get all packages from a specific source.

        Args:
            source_prefix: Source prefix to filter by
            (e.g., "COPR:", "AUR:", "official")

        Returns:
            List of PackageMapping objects matching the source

        """
        if source_prefix == "official":
            return [m for m in self.mappings.values() if m.is_official]

        return [
            m
            for m in self.mappings.values()
            if m.source.startswith(source_prefix)
        ]

    def has_mapping(self, package_name: str) -> bool:
        """Check if package has a defined mapping."""
        return package_name in self.mappings
