"""Tests for Qtile window manager configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.wm import qtile


class TestQtileConfigInstall:
    """Test QtileConfig install method."""

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    def test_install_with_packages(
        self, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test install with packages provided."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (True, "Success")
        mock_pm.return_value = mock_pm_instance

        result = qtile.install("fedora", packages=["qtile"])

        assert result is True
        mock_pm_instance.install.assert_called_once_with(["qtile"])

    def test_install_without_packages(self) -> None:
        """Test install without packages (empty list)."""
        result = qtile.install("fedora")

        assert result is True

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    def test_install_failure(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install failure."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.return_value = (False, "Installation failed")
        mock_pm.return_value = mock_pm_instance

        result = qtile.install("fedora", packages=["qtile"])

        assert result is False

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    def test_install_exception(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test install with exception during package installation."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm_instance = MagicMock()
        mock_pm_instance.install.side_effect = Exception("Network error")
        mock_pm.return_value = mock_pm_instance

        result = qtile.install("fedora", packages=["qtile"])

        assert result is False


class TestQtileConfigSetupBacklightRules:
    """Test QtileConfig setup_backlight_rules method."""

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    @patch("aps.wm.qtile.Path")
    def test_setup_backlight_rules_success(
        self,
        mock_path: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test successful setup of backlight rules."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        # Mock Path objects
        mock_configs_dir = MagicMock()
        mock_qtile_src = MagicMock()
        mock_backlight_src = MagicMock()
        mock_qtile_dest = MagicMock()
        mock_backlight_dest = MagicMock()
        mock_qtile_parent = MagicMock()
        mock_backlight_parent = MagicMock()

        mock_qtile_parent.exists.return_value = True
        mock_backlight_parent.exists.return_value = True

        mock_path.return_value.parent.parent.__truediv__ = MagicMock(
            return_value=mock_configs_dir
        )
        mock_configs_dir.__truediv__ = MagicMock(
            side_effect=[mock_qtile_src, mock_backlight_src]
        )
        mock_path.side_effect = [
            MagicMock(),  # __file__
            mock_qtile_dest,  # qtile_rules_dest
            mock_backlight_dest,  # backlight_dest
        ]
        mock_qtile_dest.parent = mock_qtile_parent
        mock_backlight_dest.parent = mock_backlight_parent

        # Mock run_privileged to succeed
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_priv.return_value = mock_result

        result = qtile.setup_backlight_rules()

        assert result is True
        # Should call run_privileged 4 times: cp qtile, cp backlight,
        # udevadm control, udevadm trigger
        assert mock_run_priv.call_count == 4

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    @patch("aps.wm.qtile.Path")
    def test_setup_backlight_rules_mkdir_failure(
        self,
        mock_path: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test setup_backlight_rules when mkdir fails."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        mock_qtile_dest = MagicMock()
        mock_backlight_dest = MagicMock()
        mock_qtile_parent = MagicMock()
        mock_backlight_parent = MagicMock()

        mock_qtile_parent.exists.return_value = False
        mock_backlight_parent.exists.return_value = True

        mock_path.side_effect = [
            MagicMock(),  # __file__
            mock_qtile_dest,
            mock_backlight_dest,
        ]
        mock_qtile_dest.parent = mock_qtile_parent
        mock_backlight_dest.parent = mock_backlight_parent

        # Mock mkdir failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run_priv.return_value = mock_result

        result = qtile.setup_backlight_rules()

        assert result is False

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    @patch("aps.wm.qtile.Path")
    def test_setup_backlight_rules_cp_qtile_failure(
        self,
        mock_path: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test setup_backlight_rules when copying qtile rules fails."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        mock_qtile_dest = MagicMock()
        mock_backlight_dest = MagicMock()
        mock_qtile_parent = MagicMock()
        mock_backlight_parent = MagicMock()

        mock_qtile_parent.exists.return_value = True
        mock_backlight_parent.exists.return_value = True

        mock_path.side_effect = [
            MagicMock(),  # __file__
            mock_qtile_dest,
            mock_backlight_dest,
        ]
        mock_qtile_dest.parent = mock_qtile_parent
        mock_backlight_dest.parent = mock_backlight_parent

        # Mock cp qtile failure
        mock_result_success = MagicMock()
        mock_result_success.returncode = 0
        mock_result_fail = MagicMock()
        mock_result_fail.returncode = 1
        mock_result_fail.stderr = "File not found"
        mock_run_priv.side_effect = [
            mock_result_fail
        ]  # First call (cp qtile) fails

        result = qtile.setup_backlight_rules()

        assert result is False

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    @patch("aps.wm.qtile.Path")
    def test_setup_backlight_rules_cp_backlight_failure(
        self,
        mock_path: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test setup_backlight_rules when copying backlight config fails."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        mock_qtile_dest = MagicMock()
        mock_backlight_dest = MagicMock()
        mock_qtile_parent = MagicMock()
        mock_backlight_parent = MagicMock()

        mock_qtile_parent.exists.return_value = True
        mock_backlight_parent.exists.return_value = True

        mock_path.side_effect = [
            MagicMock(),  # __file__
            mock_qtile_dest,
            mock_backlight_dest,
        ]
        mock_qtile_dest.parent = mock_qtile_parent
        mock_backlight_dest.parent = mock_backlight_parent

        # Mock cp qtile success, cp backlight failure
        mock_result_success = MagicMock()
        mock_result_success.returncode = 0
        mock_result_fail = MagicMock()
        mock_result_fail.returncode = 1
        mock_result_fail.stderr = "Permission denied"
        mock_run_priv.side_effect = [
            mock_result_success,
            mock_result_fail,
        ]  # cp qtile ok, cp backlight fail

        result = qtile.setup_backlight_rules()

        assert result is False

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    @patch("aps.wm.qtile.Path")
    def test_setup_backlight_rules_udev_reload_failure(
        self,
        mock_path: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test setup_backlight_rules when udevadm control fails."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        mock_qtile_dest = MagicMock()
        mock_backlight_dest = MagicMock()
        mock_qtile_parent = MagicMock()
        mock_backlight_parent = MagicMock()

        mock_qtile_parent.exists.return_value = True
        mock_backlight_parent.exists.return_value = True

        mock_path.side_effect = [
            MagicMock(),  # __file__
            mock_qtile_dest,
            mock_backlight_dest,
        ]
        mock_qtile_dest.parent = mock_qtile_parent
        mock_backlight_dest.parent = mock_backlight_parent

        # Mock cp success, udev control fail
        mock_result_success = MagicMock()
        mock_result_success.returncode = 0
        mock_result_fail = MagicMock()
        mock_result_fail.returncode = 1
        mock_result_fail.stderr = "Command not found"
        mock_run_priv.side_effect = [
            mock_result_success,
            mock_result_success,
            mock_result_fail,
        ]  # cp ok, cp ok, udev control fail

        result = qtile.setup_backlight_rules()

        assert result is False

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.run_privileged")
    @patch("aps.wm.qtile.Path")
    def test_setup_backlight_rules_udev_trigger_failure(
        self,
        mock_path: Mock,
        mock_run_priv: Mock,
        mock_pm: Mock,
        mock_distro: Mock,
    ) -> None:
        """Test setup_backlight_rules when udevadm trigger fails."""
        mock_distro.return_value = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_pm.return_value = MagicMock()

        mock_qtile_dest = MagicMock()
        mock_backlight_dest = MagicMock()
        mock_qtile_parent = MagicMock()
        mock_backlight_parent = MagicMock()

        mock_qtile_parent.exists.return_value = True
        mock_backlight_parent.exists.return_value = True

        mock_path.side_effect = [
            MagicMock(),  # __file__
            mock_qtile_dest,
            mock_backlight_dest,
        ]
        mock_qtile_dest.parent = mock_qtile_parent
        mock_backlight_dest.parent = mock_backlight_parent

        # Mock cp success, udev control success, udev trigger fail
        mock_result_success = MagicMock()
        mock_result_success.returncode = 0
        mock_result_fail = MagicMock()
        mock_result_fail.returncode = 1
        mock_result_fail.stderr = "Permission denied"
        mock_run_priv.side_effect = [
            mock_result_success,
            mock_result_success,
            mock_result_success,
            mock_result_fail,
        ]  # all cp ok, udev control ok, udev trigger fail

        result = qtile.setup_backlight_rules()

        assert result is False


class TestQtileConfigConfigure:
    """Test QtileConfig configure method."""

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.utils.privilege.run_privileged")
    def test_configure_returns_true(
        self, mock_run_priv: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test that configure always returns True."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_distro.return_value = fedora_distro
        mock_pm.return_value = MagicMock()
        mock_run_priv.return_value = MagicMock(returncode=0, stderr="")

        result = qtile.configure("fedora")

        assert result is True

    @patch("aps.wm.qtile.detect_distro")
    @patch("aps.wm.qtile.get_package_manager")
    @patch("aps.wm.qtile.setup_backlight_rules")
    def test_configure_setup_backlight_failure(
        self, mock_setup_backlight: Mock, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test configure when setup_backlight_rules fails."""
        fedora_distro = DistroInfo(
            name="Fedora Linux",
            version="39",
            id="fedora",
            id_like=[],
            package_manager=PackageManagerType.DNF,
            family=DistroFamily.FEDORA,
        )
        mock_distro.return_value = fedora_distro
        mock_pm.return_value = MagicMock()
        mock_setup_backlight.return_value = False

        result = qtile.configure("fedora")

        assert result is False
