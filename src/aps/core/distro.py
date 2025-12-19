"""Distribution detection module for identifying Linux distributions."""

import re
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Self

from .logger import get_logger

logger = get_logger(__name__)


class PackageManagerType(Enum):
    """Supported package manager types."""

    DNF = "dnf"
    PACMAN = "pacman"
    UNKNOWN = "unknown"


class DistroFamily(Enum):
    """Distribution families for shared behavior."""

    FEDORA = "fedora"
    ARCH = "arch"
    UNKNOWN = "unknown"


@dataclass
class DistroInfo:
    """Information about detected Linux distribution."""

    name: str
    version: str
    id: str
    id_like: list[str]
    package_manager: PackageManagerType
    family: DistroFamily

    @classmethod
    def from_os_release(
        cls, os_release_path: Path = Path("/etc/os-release")
    ) -> Self:
        """Detect distribution from /etc/os-release file.

        Args:
            os_release_path: Path to os-release file (default: /etc/os-release)

        Returns:
            DistroInfo object with detected distribution information

        Raises:
            FileNotFoundError: If os-release file doesn't exist
            ValueError: If required fields are missing

        """
        if not os_release_path.exists():
            raise FileNotFoundError(
                f"OS release file not found: {os_release_path}"
            )

        data = cls._parse_os_release(os_release_path)

        distro_id = data.get("ID", "").lower()
        id_like = data.get("ID_LIKE", "").lower().split()
        version = data.get("VERSION_ID", "rolling")
        name = data.get("NAME", distro_id)

        # Determine package manager and family
        pm_type, family = cls._detect_package_manager(distro_id, id_like)

        return cls(
            name=name,
            version=version,
            id=distro_id,
            id_like=id_like,
            package_manager=pm_type,
            family=family,
        )

    @staticmethod
    def _parse_os_release(path: Path) -> dict[str, str]:
        """Parse /etc/os-release file into key-value dictionary.

        Format specification: https://www.freedesktop.org/software/systemd/man/os-release.html

        Args:
            path: Path to os-release file

        Returns:
            Dictionary of key-value pairs from os-release

        """
        data: dict[str, str] = {}
        content = path.read_text(encoding="utf-8")

        # Match KEY="VALUE" or KEY=VALUE format
        pattern = re.compile(r'^([A-Z_]+)=(?:"([^"]*)"|(.*))', re.MULTILINE)

        for match in pattern.finditer(content):
            key = match.group(1)
            # Use quoted value if present, otherwise unquoted value
            value = (
                match.group(2)
                if match.group(2) is not None
                else match.group(3)
            )
            data[key] = value

        return data

    @staticmethod
    def _detect_package_manager(
        distro_id: str, id_like: list[str]
    ) -> tuple[PackageManagerType, DistroFamily]:
        """Detect package manager and distribution family.

        Uses distribution ID and ID_LIKE to determine the appropriate
        package manager. Supports derivative distributions (e.g., Nobara,
        CachyOS, Manjaro) by checking ID_LIKE relationships.

        Args:
            distro_id: Distribution ID from os-release
            id_like: List of parent distribution IDs

        Returns:
            Tuple of (PackageManagerType, DistroFamily)

        """
        # Fedora family (dnf-based)
        fedora_distros = {"fedora", "nobara", "rhel", "rocky", "almalinux"}
        if distro_id in fedora_distros or any(
            parent in fedora_distros for parent in id_like
        ):
            return PackageManagerType.DNF, DistroFamily.FEDORA

        # Arch family (pacman-based)
        arch_distros = {
            "arch",
            "archlinux",
            "manjaro",
            "cachyos",
            "endeavouros",
            "garuda",
            "artix",
        }
        if distro_id in arch_distros or any(
            parent in arch_distros for parent in id_like
        ):
            return PackageManagerType.PACMAN, DistroFamily.ARCH

        return PackageManagerType.UNKNOWN, DistroFamily.UNKNOWN


def detect_package_manager() -> PackageManagerType:
    """Detect package manager by checking for executable binaries.

    This function checks for the presence of package manager executables
    on the system to determine which package manager is available.
    This provides a more reliable detection method than relying solely
    on distribution identification.

    Returns:
        PackageManagerType enum value for detected package manager

    """
    # Check for dnf (Fedora/RHEL family)
    if shutil.which("dnf"):
        return PackageManagerType.DNF

    # Check for pacman (Arch family)
    if shutil.which("pacman"):
        return PackageManagerType.PACMAN

    return PackageManagerType.UNKNOWN


def detect_distro() -> DistroInfo:
    """Detect current distribution.

    Uses os-release file as primary detection method, with package manager
    binary detection as validation and fallback.

    Returns:
        DistroInfo object for current system

    Raises:
        FileNotFoundError: If /etc/os-release doesn't exist
        ValueError: If distribution cannot be determined

    """
    try:
        distro = DistroInfo.from_os_release()
    except FileNotFoundError as exc:
        # Fallback to package manager detection if os-release doesn't exist
        pm_type = detect_package_manager()
        if pm_type == PackageManagerType.UNKNOWN:
            raise ValueError(
                "Could not detect distribution: /etc/os-release not found and "
                "no supported package manager detected"
            ) from exc

        # Create a minimal DistroInfo based on package manager
        family = {
            PackageManagerType.DNF: DistroFamily.FEDORA,
            PackageManagerType.PACMAN: DistroFamily.ARCH,
        }.get(pm_type, DistroFamily.UNKNOWN)

        return DistroInfo(
            name=f"Unknown ({pm_type.value})",
            version="unknown",
            id="unknown",
            id_like=[],
            package_manager=pm_type,
            family=family,
        )

    # Validate os-release detection with package manager detection
    detected_pm = detect_package_manager()

    if distro.package_manager == PackageManagerType.UNKNOWN:
        # If os-release didn't give us a package manager, use binary detection
        if detected_pm != PackageManagerType.UNKNOWN:
            logger.warning(
                "Distribution family not determined from os-release (%s). "
                "Using PM detection (%s).",
                distro.id,
                detected_pm.value,
            )
            distro.package_manager = detected_pm
            distro.family = {
                PackageManagerType.DNF: DistroFamily.FEDORA,
                PackageManagerType.PACMAN: DistroFamily.ARCH,
            }.get(detected_pm, DistroFamily.UNKNOWN)
        else:
            logger.error(
                "Could not detect distribution: os-release shows unsupported "
                "distribution '%s' and no supported package manager found. "
                "Supported: Fedora (dnf), Arch (pacman)",
                distro.id,
            )
            raise ValueError(
                f"Unsupported distribution: {distro.id}. "
                f"Supported: Fedora (dnf), Arch (pacman)"
            )
    elif detected_pm not in (
        PackageManagerType.UNKNOWN,
        distro.package_manager,
    ):
        # Mismatch between os-release and binary detection, prefer PM
        logger.warning(
            "Package manager mismatch detected: os-release indicates %s, "
            "but %s binary found. Preferring PM detection (%s).",
            distro.package_manager.value,
            detected_pm.value,
            detected_pm.value,
        )
        # Update to use package manager detection
        distro.package_manager = detected_pm
        distro.family = {
            PackageManagerType.DNF: DistroFamily.FEDORA,
            PackageManagerType.PACMAN: DistroFamily.ARCH,
        }.get(detected_pm, DistroFamily.UNKNOWN)

    return distro
