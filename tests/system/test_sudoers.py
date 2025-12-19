"""Tests for sudoers configuration module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aps.core.distro import DistroFamily, DistroInfo, PackageManagerType
from aps.system.sudoers import SudoersConfig

EXPECTED_RUN_PRIVILEGED_CALLS = 2


class TestSudoersConfig:
    """Tests for Sudoers configuration."""

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    def test_init(self, mock_get_pm: Mock, mock_detect_distro: Mock) -> None:
        """Test SudoersConfig initialization."""
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

        sudoers = SudoersConfig()
        assert sudoers.sudoers_file == Path("/etc/sudoers")

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.SudoersConfig.configure_terminal_timeout")
    def test_configure_success(
        self,
        mock_configure_timeout: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful configuration."""
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
        mock_configure_timeout.return_value = True

        sudoers = SudoersConfig()
        result = sudoers.configure()

        assert result is True
        mock_configure_timeout.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.SudoersConfig.configure_terminal_timeout")
    def test_configure_failure(
        self,
        mock_configure_timeout: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test configuration failure."""
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
        mock_configure_timeout.return_value = False

        sudoers = SudoersConfig()
        result = sudoers.configure()

        assert result is False
        mock_configure_timeout.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    @patch("aps.system.sudoers.SudoersConfig._create_backup")
    @patch("aps.system.sudoers.SudoersConfig._validate_sudoers")
    @patch("aps.system.sudoers.SudoersConfig._update_sudoers_section")
    def test_configure_terminal_timeout_success(
        self,
        mock_update_section: Mock,
        mock_validate: Mock,
        mock_create_backup: Mock,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful terminal timeout configuration."""
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
        mock_create_backup.return_value = True
        mock_update_section.return_value = True
        mock_validate.return_value = True

        sudoers = SudoersConfig()
        result = sudoers.configure_terminal_timeout()

        assert result is True
        mock_create_backup.assert_called_once()
        mock_update_section.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.SudoersConfig._create_backup")
    def test_configure_terminal_timeout_backup_failure(
        self,
        mock_create_backup: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test terminal timeout configuration when backup fails."""
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
        mock_create_backup.return_value = False

        sudoers = SudoersConfig()
        result = sudoers.configure_terminal_timeout()

        assert result is False
        mock_create_backup.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    @patch("aps.system.sudoers.SudoersConfig._create_backup")
    @patch("aps.system.sudoers.Path.read_text")
    def test_configure_terminal_timeout_validation_failure(
        self,
        mock_read_text: Mock,
        mock_create_backup: Mock,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test terminal timeout configuration when validation fails."""
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
        mock_create_backup.return_value = True
        mock_read_text.return_value = "existing content"

        # Mock tee success, visudo failure
        mock_run_privileged.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # tee
            Mock(returncode=1, stdout="", stderr=""),  # visudo
        ]

        sudoers = SudoersConfig()
        with patch.object(
            sudoers, "_restore_latest_backup", return_value=True
        ):
            result = sudoers.configure_terminal_timeout()

        assert result is False
        mock_create_backup.assert_called_once()
        assert mock_run_privileged.call_count == EXPECTED_RUN_PRIVILEGED_CALLS

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    @patch("aps.system.sudoers.Path.read_text")
    def test_update_sudoers_section_existing(
        self,
        mock_read_text: Mock,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test updating sudoers section when existing section present."""
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
        mock_read_text.return_value = (
            "existing content\n# START\nold config\n# END\nmore content"
        )
        mock_run_privileged.return_value = Mock(returncode=0)

        sudoers = SudoersConfig()
        result = sudoers._update_sudoers_section(
            "# START", "# END", "new config"
        )

        assert result is True
        mock_run_privileged.assert_called()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.Path.read_text")
    def test_update_sudoers_section_exception(
        self,
        mock_read_text: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test updating sudoers section when read_text raises exception."""
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
        mock_read_text.side_effect = OSError("Permission denied")

        sudoers = SudoersConfig()
        result = sudoers._update_sudoers_section(
            "# START", "# END", "new config"
        )

        assert result is False

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_create_backup_success(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful backup creation."""
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
        mock_run_privileged.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )

        sudoers = SudoersConfig()
        result = sudoers._create_backup()

        assert result is True
        mock_run_privileged.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_create_backup_failure(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test backup creation failure."""
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
        mock_run_privileged.return_value = Mock(
            returncode=1, stdout="", stderr=""
        )

        sudoers = SudoersConfig()
        result = sudoers._create_backup()

        assert result is False
        mock_run_privileged.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_validate_sudoers_success(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful sudoers validation."""
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
        mock_run_privileged.return_value = Mock(
            returncode=0, stdout="", stderr=""
        )

        sudoers = SudoersConfig()
        result = sudoers._validate_sudoers()

        assert result is True
        mock_run_privileged.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_validate_sudoers_failure(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test sudoers validation failure."""
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
        mock_run_privileged.return_value = Mock(
            returncode=1, stdout="", stderr=""
        )

        sudoers = SudoersConfig()
        result = sudoers._validate_sudoers()

        assert result is False
        mock_run_privileged.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_restore_latest_backup_success(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test successful backup restoration."""
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
        mock_run_privileged.side_effect = [
            Mock(
                returncode=0,
                stdout="/etc/sudoers.bak.20231218120000\n/etc/sudoers.bak.20231218110000",
                stderr="",
            ),
            Mock(returncode=0, stdout="", stderr=""),
        ]

        sudoers = SudoersConfig()
        result = sudoers._restore_latest_backup()

        assert result is True
        assert mock_run_privileged.call_count == EXPECTED_RUN_PRIVILEGED_CALLS

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_restore_latest_backup_no_backups(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test backup restoration when no backups exist."""
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
        mock_run_privileged.return_value = Mock(
            returncode=1, stdout="", stderr=""
        )

        sudoers = SudoersConfig()
        result = sudoers._restore_latest_backup()

        assert result is False
        mock_run_privileged.assert_called_once()

    @patch("aps.system.base.detect_distro")
    @patch("aps.system.base.get_package_manager")
    @patch("aps.system.sudoers.run_privileged")
    def test_restore_latest_backup_restore_failure(
        self,
        mock_run_privileged: Mock,
        mock_get_pm: Mock,
        mock_detect_distro: Mock,
    ) -> None:
        """Test backup restoration when restore command fails."""
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
        mock_run_privileged.side_effect = [
            Mock(
                returncode=0,
                stdout="/etc/sudoers.bak.20231218120000",
                stderr="",
            ),
            Mock(returncode=1, stdout="", stderr=""),
        ]

        sudoers = SudoersConfig()
        result = sudoers._restore_latest_backup()

        assert result is False
        assert mock_run_privileged.call_count == EXPECTED_RUN_PRIVILEGED_CALLS
