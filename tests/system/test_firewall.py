"""Tests for firewall configuration module."""

from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.firewall import UFWConfig


class TestUFWConfig:
    """Tests for UFW firewall configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful UFW configuration."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(
                ufw, "_configure_default_policies", return_value=True
            ),
            patch.object(ufw, "_configure_syncthing_rules", return_value=True),
            patch.object(ufw, "_enable_ufw", return_value=True),
        ):
            result = ufw.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_ufw_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful UFW disabling."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()
        result = ufw._disable_ufw()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_enable_ufw_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test successful UFW enabling."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()
        result = ufw._enable_ufw()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_disable_firewalld_fails(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW config when disabling firewalld fails (but continues)."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=False),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(
                ufw, "_configure_default_policies", return_value=True
            ),
            patch.object(ufw, "_configure_syncthing_rules", return_value=True),
            patch.object(ufw, "_enable_ufw", return_value=True),
        ):
            result = ufw.configure()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_disable_ufw_fails(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW configuration fails when disabling UFW fails."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=False),
        ):
            result = ufw.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_ssh_rules_fails(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW configuration fails when SSH rules fail."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=False),
        ):
            result = ufw.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_default_policies_fails(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW configuration fails when default policies fail."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(
                ufw, "_configure_default_policies", return_value=False
            ),
        ):
            result = ufw.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_syncthing_rules_fails(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW configuration fails when Syncthing rules fail."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(
                ufw, "_configure_default_policies", return_value=True
            ),
            patch.object(
                ufw, "_configure_syncthing_rules", return_value=False
            ),
        ):
            result = ufw.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_enable_ufw_fails(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW configuration fails when enabling UFW fails."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with (
            patch.object(ufw, "_disable_firewalld", return_value=True),
            patch.object(ufw, "_disable_ufw", return_value=True),
            patch.object(ufw, "_configure_ssh_rules", return_value=True),
            patch.object(
                ufw, "_configure_default_policies", return_value=True
            ),
            patch.object(ufw, "_configure_syncthing_rules", return_value=True),
            patch.object(ufw, "_enable_ufw", return_value=False),
        ):
            result = ufw.configure()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_ufw_failure(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW disabling failure."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = ufw._disable_ufw()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_ufw_exception(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW disabling with exception."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch(
            "aps.system.firewall.run_privileged",
            side_effect=Exception("Test exception"),
        ):
            result = ufw._disable_ufw()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_enable_ufw_failure(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW enabling failure."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = ufw._enable_ufw()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_enable_ufw_exception(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test UFW enabling with exception."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch(
            "aps.system.firewall.run_privileged",
            side_effect=Exception("Test exception"),
        ):
            result = ufw._enable_ufw()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_firewalld_firewalld_found(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test disabling firewalld when it exists."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("subprocess.run") as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            result = ufw._disable_firewalld()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_firewalld_firewalld_not_found(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test disabling firewalld when it does not exist."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("subprocess.run") as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_subprocess.return_value = mock_result
            result = ufw._disable_firewalld()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_disable_firewalld_exception(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test disabling firewalld with exception."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("subprocess.run", side_effect=Exception("Test exception")):
            result = ufw._disable_firewalld()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_ssh_rules_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring SSH rules successfully."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = ufw._configure_ssh_rules()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_ssh_rules_failure(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring SSH rules failure."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")
            result = ufw._configure_ssh_rules()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_ssh_rules_exception(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring SSH rules with exception."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch(
            "aps.system.firewall.run_privileged",
            side_effect=Exception("Test exception"),
        ):
            result = ufw._configure_ssh_rules()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_default_policies_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring default policies successfully."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = ufw._configure_default_policies()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_default_policies_failure(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring default policies failure."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")
            result = ufw._configure_default_policies()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_default_policies_exception(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring default policies with exception."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch(
            "aps.system.firewall.run_privileged",
            side_effect=Exception("Test exception"),
        ):
            result = ufw._configure_default_policies()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_syncthing_rules_success(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring Syncthing rules successfully."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = ufw._configure_syncthing_rules()

        assert result is True

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_syncthing_rules_failure(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring Syncthing rules failure."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch("aps.system.firewall.run_privileged") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")
            result = ufw._configure_syncthing_rules()

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_configure_syncthing_rules_exception(
        self, mock_get_pm: Mock, mock_detect_distro: Mock
    ) -> None:
        """Test configuring Syncthing rules with exception."""
        debian_distro = DistroInfo(
            name="Debian GNU/Linux",
            version="12",
            id="debian",
            id_like=[],
            package_manager=PackageManagerType.APT,
            family=DistroFamily.DEBIAN,
        )
        mock_detect_distro.return_value = debian_distro
        mock_get_pm.return_value = MagicMock()

        ufw = UFWConfig()

        with patch(
            "aps.system.firewall.run_privileged",
            side_effect=Exception("Test exception"),
        ):
            result = ufw._configure_syncthing_rules()

        assert result is False
