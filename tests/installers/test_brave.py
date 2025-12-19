# Import DistroInfo for use in tests
from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType

"""Tests for Brave browser installer module."""

from unittest.mock import MagicMock, patch

from aps.installers.brave import BraveInstaller


class TestBraveInstaller:
    """Tests for Brave Browser installer."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_is_installed_when_brave_exists(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test _is_installed returns True when brave command exists."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with patch(
            "aps.installers.brave.shutil.which", return_value="/usr/bin/brave"
        ):
            assert installer._is_installed() is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_is_installed_when_brave_not_exists(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test _is_installed returns False when brave command doesn't exist."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with patch("aps.installers.brave.shutil.which", return_value=None):
            assert installer._is_installed() is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_already_installed(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test install when Brave is already installed."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with (
            patch.object(installer, "_is_installed", return_value=True),
            patch.object(installer, "_disable_keyring", return_value=True),
        ):
            result = installer.install()

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_curl_not_available(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test install fails when curl is not available."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with (
            patch.object(installer, "_is_installed", return_value=False),
            patch("aps.installers.brave.shutil.which", return_value=None),
        ):
            result = installer.install()

        assert result is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_success(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test successful Brave installation."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with (
            patch.object(installer, "_is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch.object(installer, "_install_brave", return_value=True),
            patch.object(installer, "_disable_keyring", return_value=True),
        ):
            result = installer.install()

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_brave_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test install fails when _install_brave fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with (
            patch.object(installer, "_is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch.object(installer, "_install_brave", return_value=False),
        ):
            result = installer.install()

        assert result is False

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_arch_success(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test successful Brave installation on Arch."""
        arch_distro = DistroInfo(
            name="Arch Linux",
            version="rolling",
            id="arch",
            id_like=["archlinux"],
            package_manager=PackageManagerType.PACMAN,
            family=DistroFamily.ARCH,
        )
        mock_detect_distro.return_value = arch_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with (
            patch.object(installer, "_is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch.object(installer, "_install_brave", return_value=True),
            patch.object(installer, "_disable_keyring", return_value=True),
        ):
            result = installer.install()

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_install_disable_keyring_fail(
        self, mock_get_pm: MagicMock, mock_detect_distro: MagicMock
    ) -> None:
        """Test install succeeds but warns when _disable_keyring fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_detect_distro.return_value = fedora_distro
        mock_get_pm.return_value = MagicMock()

        installer = BraveInstaller()

        with (
            patch.object(installer, "_is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch.object(installer, "_install_brave", return_value=True),
            patch.object(installer, "_disable_keyring", return_value=False),
        ):
            result = installer.install()

        assert result is True
