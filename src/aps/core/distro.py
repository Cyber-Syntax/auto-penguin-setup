"""Distribution detection module for identifying Linux distributions."""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Self


class PackageManagerType(Enum):
    """Supported package manager types."""

    DNF = "dnf"
    PACMAN = "pacman"
    APT = "apt"
    UNKNOWN = "unknown"


class DistroFamily(Enum):
    """Distribution families for shared behavior."""

    FEDORA = "fedora"
    ARCH = "arch"
    DEBIAN = "debian"
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
    def from_os_release(cls, os_release_path: Path = Path("/etc/os-release")) -> Self:
        """
        Detect distribution from /etc/os-release file.

        Args:
            os_release_path: Path to os-release file (default: /etc/os-release)

        Returns:
            DistroInfo object with detected distribution information

        Raises:
            FileNotFoundError: If os-release file doesn't exist
            ValueError: If required fields are missing
        """
        if not os_release_path.exists():
            raise FileNotFoundError(f"OS release file not found: {os_release_path}")

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
        """
        Parse /etc/os-release file into key-value dictionary.

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
            value = match.group(2) if match.group(2) is not None else match.group(3)
            data[key] = value

        return data

    @staticmethod
    def _detect_package_manager(
        distro_id: str, id_like: list[str]
    ) -> tuple[PackageManagerType, DistroFamily]:
        """
        Detect package manager and distribution family.

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
        fedora_distros = {"fedora", "nobara", "rhel", "centos", "rocky", "almalinux"}
        if distro_id in fedora_distros or any(parent in fedora_distros for parent in id_like):
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
        if distro_id in arch_distros or any(parent in arch_distros for parent in id_like):
            return PackageManagerType.PACMAN, DistroFamily.ARCH

        # Debian family (apt-based)
        debian_distros = {"debian", "ubuntu", "linuxmint", "pop", "elementary", "kali"}
        if distro_id in debian_distros or any(parent in debian_distros for parent in id_like):
            return PackageManagerType.APT, DistroFamily.DEBIAN

        return PackageManagerType.UNKNOWN, DistroFamily.UNKNOWN


def detect_distro() -> DistroInfo:
    """
    Convenience function to detect current distribution.

    Returns:
        DistroInfo object for current system

    Raises:
        FileNotFoundError: If /etc/os-release doesn't exist
        ValueError: If distribution cannot be determined
    """
    distro = DistroInfo.from_os_release()

    if distro.package_manager == PackageManagerType.UNKNOWN:
        raise ValueError(
            f"Unsupported distribution: {distro.id}. "
            f"Supported families: Fedora (dnf), Arch (pacman), Debian (apt)"
        )

    return distro
