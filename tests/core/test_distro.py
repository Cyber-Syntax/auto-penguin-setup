"""Tests for distribution detection module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pytest import LogCaptureFixture

from aps.core.distro import (
    DistroFamily,
    DistroInfo,
    PackageManagerType,
    detect_distro,
    detect_package_manager,
)


class TestDistroInfo:
    """Test DistroInfo class and detection."""

    def test_from_os_release_fedora(
        self, sample_os_release_fedora: Path
    ) -> None:
        """Test parsing Fedora os-release."""
        distro = DistroInfo.from_os_release(sample_os_release_fedora)

        assert distro.id == "fedora"
        assert distro.name == "Fedora Linux"
        assert distro.version == "39"
        assert distro.package_manager == PackageManagerType.DNF
        assert distro.family == DistroFamily.FEDORA

    def test_from_os_release_arch(self, sample_os_release_arch: Path) -> None:
        """Test parsing Arch os-release."""
        distro = DistroInfo.from_os_release(sample_os_release_arch)

        assert distro.id == "arch"
        assert distro.name == "Arch Linux"
        assert distro.package_manager == PackageManagerType.PACMAN
        assert distro.family == DistroFamily.ARCH

    def test_from_os_release_debian(
        self, sample_os_release_debian: Path
    ) -> None:
        """Test parsing Debian os-release."""
        distro = DistroInfo.from_os_release(sample_os_release_debian)

        assert distro.id == "debian"
        assert distro.name == "Debian GNU/Linux"
        assert distro.version == "12"
        assert distro.package_manager == PackageManagerType.APT
        assert distro.family == DistroFamily.DEBIAN

    def test_from_os_release_missing_file(self, tmp_path: Path) -> None:
        """Test handling of missing os-release file."""
        with pytest.raises(FileNotFoundError):
            DistroInfo.from_os_release(tmp_path / "nonexistent")

    def test_derivative_distro_nobara(self, tmp_path: Path) -> None:
        """Test detection of Nobara (Fedora derivative)."""
        content = """
NAME="Nobara Linux"
ID=nobara
ID_LIKE=fedora
VERSION_ID=39
"""
        os_release = tmp_path / "os-release-nobara"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.family == DistroFamily.FEDORA
        assert distro.package_manager == PackageManagerType.DNF

    def test_derivative_distro_cachyos(self, tmp_path: Path) -> None:
        """Test detection of CachyOS (Arch derivative)."""
        content = """
NAME="CachyOS"
ID=cachyos
ID_LIKE=arch
"""
        os_release = tmp_path / "os-release-cachyos"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.family == DistroFamily.ARCH
        assert distro.package_manager == PackageManagerType.PACMAN

    def test_derivative_distro_ubuntu(self, tmp_path: Path) -> None:
        """Test detection of Ubuntu (Debian derivative)."""
        content = """
NAME="Ubuntu"
ID=ubuntu
ID_LIKE=debian
VERSION_ID=22.04
"""
        os_release = tmp_path / "os-release-ubuntu"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.family == DistroFamily.DEBIAN
        assert distro.package_manager == PackageManagerType.APT

    def test_from_os_release_unknown(self, tmp_path: Path) -> None:
        """Test parsing unknown distribution os-release."""
        content = """
NAME="Unknown Distro"
ID=unknown
VERSION_ID=1.0
"""
        os_release = tmp_path / "os-release-unknown"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.id == "unknown"
        assert distro.name == "Unknown Distro"
        assert distro.version == "1.0"
        assert distro.package_manager == PackageManagerType.UNKNOWN
        assert distro.family == DistroFamily.UNKNOWN

    def test_rolling_version_default(self, tmp_path: Path) -> None:
        """Test default version for rolling release."""
        content = """
NAME="Arch Linux"
ID=arch
"""
        os_release = tmp_path / "os-release-arch-rolling"
        os_release.write_text(content)

        distro = DistroInfo.from_os_release(os_release)
        assert distro.version == "rolling"

    def test_parse_os_release_quoted_values(self, tmp_path: Path) -> None:
        """Test parsing os-release with quoted values."""
        content = """
NAME="Test Distribution"
ID="test"
VERSION="1.0"
"""
        os_release = tmp_path / "os-release-quoted"
        os_release.write_text(content)

        data = DistroInfo._parse_os_release(os_release)
        assert data["NAME"] == "Test Distribution"
        assert data["ID"] == "test"
        assert data["VERSION"] == "1.0"

    def test_parse_os_release_unquoted_values(self, tmp_path: Path) -> None:
        """Test parsing os-release with unquoted values."""
        content = """
NAME=TestDistro
ID=test
"""
        os_release = tmp_path / "os-release-unquoted"
        os_release.write_text(content)

        data = DistroInfo._parse_os_release(os_release)
        assert data["NAME"] == "TestDistro"
        assert data["ID"] == "test"


class TestPackageManagerDetection:
    """Test package manager binary detection."""

    @patch("shutil.which")
    def test_detect_package_manager_dnf(self, mock_which: Mock) -> None:
        """Test detection of dnf package manager."""
        mock_which.side_effect = lambda cmd: cmd == "dnf"
        result = detect_package_manager()
        assert result == PackageManagerType.DNF

    @patch("shutil.which")
    def test_detect_package_manager_pacman(self, mock_which: Mock) -> None:
        """Test detection of pacman package manager."""
        mock_which.side_effect = lambda cmd: cmd == "pacman"
        result = detect_package_manager()
        assert result == PackageManagerType.PACMAN

    @patch("shutil.which")
    def test_detect_package_manager_apt(self, mock_which: Mock) -> None:
        """Test detection of apt package manager."""
        mock_which.side_effect = lambda cmd: cmd == "apt"
        result = detect_package_manager()
        assert result == PackageManagerType.APT

    @patch("shutil.which")
    def test_detect_package_manager_unknown(self, mock_which: Mock) -> None:
        """Test detection when no supported package manager is found."""
        mock_which.return_value = None
        result = detect_package_manager()
        assert result == PackageManagerType.UNKNOWN

    @patch("shutil.which")
    def test_detect_package_manager_priority(self, mock_which: Mock) -> None:
        """Test that dnf is detected first when multiple are available."""
        mock_which.side_effect = lambda cmd: cmd in ["dnf", "pacman", "apt"]
        result = detect_package_manager()
        assert result == PackageManagerType.DNF


class TestDetectDistro:
    """Test detect_distro() function with various scenarios."""

    @patch("aps.core.distro.detect_package_manager")
    def test_detect_distro_normal_fedora(
        self, mock_pm_detect: Mock, sample_os_release_fedora: Path
    ) -> None:
        """Test normal detection with matching os-release and package manager."""
        mock_pm_detect.return_value = PackageManagerType.DNF

        with patch(
            "aps.core.distro.DistroInfo.from_os_release"
        ) as mock_from_os:
            mock_from_os.return_value = DistroInfo(
                name="Fedora Linux",
                version="39",
                id="fedora",
                id_like=[],
                package_manager=PackageManagerType.DNF,
                family=DistroFamily.FEDORA,
            )

            distro = detect_distro()

            assert distro.package_manager == PackageManagerType.DNF
            assert distro.family == DistroFamily.FEDORA

    @patch("aps.core.distro.detect_package_manager")
    def test_detect_distro_mismatch_prefers_pm(
        self, mock_pm_detect: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test mismatch detection prefers package manager over os-release."""
        mock_pm_detect.return_value = PackageManagerType.PACMAN

        with patch(
            "aps.core.distro.DistroInfo.from_os_release"
        ) as mock_from_os:
            # os-release says DNF, but pacman binary is found
            mock_from_os.return_value = DistroInfo(
                name="Test Distro",
                version="1.0",
                id="test",
                id_like=[],
                package_manager=PackageManagerType.DNF,
                family=DistroFamily.FEDORA,
            )

            distro = detect_distro()

            # Should prefer package manager detection
            assert distro.package_manager == PackageManagerType.PACMAN
            assert distro.family == DistroFamily.ARCH

            # Should log warning about mismatch
            assert "Package manager mismatch detected" in caplog.text
            assert (
                "Preferring package manager detection (pacman)" in caplog.text
            )

    @patch("aps.core.distro.detect_package_manager")
    def test_detect_distro_unknown_os_release_fallback_to_pm(
        self, mock_pm_detect: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test fallback to package manager when os-release shows unknown."""
        mock_pm_detect.return_value = PackageManagerType.DNF

        with patch(
            "aps.core.distro.DistroInfo.from_os_release"
        ) as mock_from_os:
            # os-release returns UNKNOWN family
            mock_from_os.return_value = DistroInfo(
                name="Unknown Distro",
                version="1.0",
                id="unknown",
                id_like=[],
                package_manager=PackageManagerType.UNKNOWN,
                family=DistroFamily.UNKNOWN,
            )

            distro = detect_distro()

            # Should use package manager detection
            assert distro.package_manager == PackageManagerType.DNF
            assert distro.family == DistroFamily.FEDORA

            # Should log warning about fallback
            assert (
                "Distribution family could not be determined from os-release"
                in caplog.text
            )
            assert (
                "Using package manager detection (dnf) instead" in caplog.text
            )

    @patch("aps.core.distro.detect_package_manager")
    def test_detect_distro_both_unknown_raises_error(
        self, mock_pm_detect: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test error when both os-release and package manager detection fail."""
        mock_pm_detect.return_value = PackageManagerType.UNKNOWN

        with patch(
            "aps.core.distro.DistroInfo.from_os_release"
        ) as mock_from_os:
            # Both methods return UNKNOWN
            mock_from_os.return_value = DistroInfo(
                name="Unknown Distro",
                version="1.0",
                id="unknown",
                id_like=[],
                package_manager=PackageManagerType.UNKNOWN,
                family=DistroFamily.UNKNOWN,
            )

            with pytest.raises(
                ValueError, match="Unsupported distribution: unknown"
            ):
                detect_distro()

            # Should log error message
            assert "Could not detect distribution" in caplog.text
            assert "no supported package manager found" in caplog.text

    @patch("aps.core.distro.detect_package_manager")
    def test_detect_distro_os_release_missing_uses_pm(
        self, mock_pm_detect: Mock
    ) -> None:
        """Test fallback to package manager when os-release file is missing."""
        mock_pm_detect.return_value = PackageManagerType.PACMAN

        with patch(
            "aps.core.distro.DistroInfo.from_os_release"
        ) as mock_from_os:
            mock_from_os.side_effect = FileNotFoundError(
                "/etc/os-release not found"
            )

            distro = detect_distro()

            # Should create distro info from package manager
            assert distro.package_manager == PackageManagerType.PACMAN
            assert distro.family == DistroFamily.ARCH
            assert distro.name == "Unknown (pacman)"

    @patch("aps.core.distro.detect_package_manager")
    def test_detect_distro_os_release_missing_no_pm_raises(
        self, mock_pm_detect: Mock
    ) -> None:
        """Test error when os-release is missing and no package manager found."""
        mock_pm_detect.return_value = PackageManagerType.UNKNOWN

        with patch(
            "aps.core.distro.DistroInfo.from_os_release"
        ) as mock_from_os:
            mock_from_os.side_effect = FileNotFoundError(
                "/etc/os-release not found"
            )

            with pytest.raises(
                ValueError, match="Could not detect distribution"
            ):
                detect_distro()
