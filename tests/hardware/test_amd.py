"""Tests for AMD CPU configuration module."""

from unittest.mock import Mock, patch
from unittest.mock import mock_open as mock_open_func

from pytest import LogCaptureFixture

from aps.hardware.amd import AMDConfig


class TestAMDConfigInit:
    """Test AMDConfig initialization."""

    def test_init_fedora(self) -> None:
        """Test initialization with fedora distro."""
        config = AMDConfig("fedora")
        assert config.distro == "fedora"
        assert config.logger is not None

    def test_init_arch(self) -> None:
        """Test initialization with arch distro."""
        config = AMDConfig("arch")
        assert config.distro == "arch"


class TestAMDConfigDetection:
    """Test AMD CPU and module detection."""

    @patch("pathlib.Path.open", create=True)
    def test_is_amd_cpu_true(self, mock_open: Mock) -> None:
        """Test AMD CPU detection when AMD is present."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "AMD Ryzen 5000\n"
        )
        config = AMDConfig("fedora")

        result = config._is_amd_cpu()  # type: ignore[attr-defined]

        assert result is True

    @patch("pathlib.Path.open", create=True)
    def test_is_amd_cpu_false(self, mock_open: Mock) -> None:
        """Test AMD CPU detection when AMD is not present."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "Intel Core i7\n"
        )
        config = AMDConfig("fedora")

        result = config._is_amd_cpu()  # type: ignore[attr-defined]

        assert result is False

    @patch("pathlib.Path.open", side_effect=FileNotFoundError)
    def test_is_amd_cpu_file_not_found(
        self, mock_open: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test AMD CPU detection when cpuinfo is not found."""
        caplog.set_level("WARNING")
        config = AMDConfig("fedora")

        result = config._is_amd_cpu()  # type: ignore[attr-defined]

        assert result is False
        assert "Cannot detect CPU type" in caplog.text

    @patch("subprocess.run")
    def test_is_k10temp_loaded_true(self, mock_run: Mock) -> None:
        """Test k10temp module detection when loaded."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="k10temp 16384 0\nother modules\n"),
            Mock(returncode=0, stdout="k10temp 16384 0\n"),
        ]
        config = AMDConfig("fedora")

        result = config._is_k10temp_loaded()  # type: ignore[attr-defined]

        assert result is True
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_is_k10temp_loaded_false(self, mock_run: Mock) -> None:
        """Test k10temp module detection when not loaded."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="acpi_power_meter\nother\n"),
            Mock(returncode=1, stdout=""),
        ]
        config = AMDConfig("fedora")

        result = config._is_k10temp_loaded()  # type: ignore[attr-defined]

        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_is_k10temp_loaded_lsmod_not_found(self, mock_run: Mock) -> None:
        """Test k10temp detection when lsmod is not found."""
        config = AMDConfig("fedora")

        result = config._is_k10temp_loaded()  # type: ignore[attr-defined]

        assert result is False

    @patch("subprocess.run")
    def test_is_zenpower_loaded_true(self, mock_run: Mock) -> None:
        """Test zenpower module detection when loaded."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="zenpower 16384 0\nother modules\n"),
            Mock(returncode=0, stdout="zenpower 16384 0\n"),
        ]
        config = AMDConfig("fedora")

        result = config._is_zenpower_loaded()  # type: ignore[attr-defined]

        assert result is True

    @patch("subprocess.run")
    def test_is_zenpower_loaded_false(self, mock_run: Mock) -> None:
        """Test zenpower module detection when not loaded."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="acpi_power_meter\nother\n"),
            Mock(returncode=1, stdout=""),
        ]
        config = AMDConfig("fedora")

        result = config._is_zenpower_loaded()  # type: ignore[attr-defined]

        assert result is False

    @patch("subprocess.run")
    def test_is_zenpower_loaded_lsmod_fails(self, mock_run: Mock) -> None:
        """Test zenpower detection when lsmod fails."""
        mock_run.return_value = Mock(returncode=1)
        config = AMDConfig("fedora")

        result = config._is_zenpower_loaded()  # type: ignore[attr-defined]

        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_is_zenpower_loaded_lsmod_not_found(self, mock_run: Mock) -> None:
        """Test zenpower detection when lsmod is not found."""
        config = AMDConfig("fedora")

        result = config._is_zenpower_loaded()  # type: ignore[attr-defined]

        assert result is False

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_is_k10temp_blacklisted_modprobe_dir_not_exists(
        self, mock_exists: Mock, mock_glob: Mock
    ) -> None:
        """Test k10temp blacklist check when modprobe.d doesn't exist."""
        mock_exists.return_value = False
        config = AMDConfig("fedora")

        result = config._is_k10temp_blacklisted()  # type: ignore[attr-defined]

        assert result is False
        mock_exists.assert_called_once()
        mock_glob.assert_not_called()

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_is_k10temp_blacklisted_no_conf_files(
        self, mock_exists: Mock, mock_glob: Mock
    ) -> None:
        """Test k10temp blacklist check when no conf files exist."""
        mock_exists.return_value = True
        mock_glob.return_value = []
        config = AMDConfig("fedora")

        result = config._is_k10temp_blacklisted()  # type: ignore[attr-defined]

        assert result is False
        mock_glob.assert_called_once_with("*.conf")

    def test_is_k10temp_blacklisted_no_blacklist_in_files(self) -> None:
        """Test k10temp blacklist check when conf files don't contain blacklist."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.glob") as mock_glob,
        ):
            mock_file = Mock()
            mock_file.open = mock_open_func(read_data="some content")
            mock_glob.return_value = [mock_file]
            config = AMDConfig("fedora")

            result = config._is_k10temp_blacklisted()  # type: ignore[attr-defined]

            assert result is False

    def test_is_k10temp_blacklisted_found_blacklist(self) -> None:
        """Test k10temp blacklist check when blacklist is found."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.glob") as mock_glob,
        ):
            mock_file = Mock()
            mock_file.open = mock_open_func(read_data="blacklist k10temp")
            mock_glob.return_value = [mock_file]
            config = AMDConfig("fedora")

            result = config._is_k10temp_blacklisted()  # type: ignore[attr-defined]

            assert result is True

    def test_is_k10temp_blacklisted_oserror_open(self) -> None:
        """Test k10temp blacklist check when OSError opening file."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.glob") as mock_glob,
        ):
            mock_file = Mock()
            mock_file.open.side_effect = OSError
            mock_glob.return_value = [mock_file]
            config = AMDConfig("fedora")

            result = config._is_k10temp_blacklisted()  # type: ignore[attr-defined]

            assert result is False


class TestAMDConfigSetupZenpower:
    """Test zenpower setup functionality."""

    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_loaded")
    def test_setup_zenpower_no_amd_cpu(
        self, mock_k10temp: Mock, mock_amd: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test setup fails when AMD CPU not detected."""
        caplog.set_level("ERROR")
        mock_amd.return_value = False
        config = AMDConfig("fedora")

        result = config.setup_zenpower()

        assert result is False
        assert "does not appear to have an AMD CPU" in caplog.text

    @patch("aps.hardware.amd.run_privileged")
    @patch("pathlib.Path.open", create=True)
    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_blacklisted")
    @patch("aps.hardware.amd.AMDConfig._load_zenpower_module")
    @patch("subprocess.run")
    def test_setup_zenpower_fedora_success(
        self,
        mock_subprocess: Mock,
        mock_load: Mock,
        mock_blacklisted: Mock,
        mock_amd: Mock,
        mock_open: Mock,
        mock_priv: Mock,
    ) -> None:
        """Test successful zenpower setup on Fedora."""
        mock_amd.return_value = True
        mock_blacklisted.return_value = False
        mock_subprocess.return_value = Mock(stdout="k10temp 16384 0\n")
        mock_priv.return_value = Mock(returncode=0)
        mock_load.return_value = True
        config = AMDConfig("fedora")

        result = config.setup_zenpower()

        assert result is True

    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_loaded")
    def test_setup_zenpower_unsupported_distro(
        self, mock_k10temp: Mock, mock_amd: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test setup fails with unsupported distribution."""
        caplog.set_level("ERROR")
        mock_amd.return_value = True
        mock_k10temp.return_value = False
        config = AMDConfig("unsupported")

        result = config.setup_zenpower()

        assert result is False
        assert "Unsupported distribution" in caplog.text

    @patch("aps.hardware.amd.run_privileged")
    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_loaded")
    def test_setup_zenpower_unload_k10temp_fails(
        self,
        mock_k10temp_loaded: Mock,
        mock_amd: Mock,
        mock_priv: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test setup fails when unloading k10temp fails."""
        caplog.set_level("ERROR")
        mock_amd.return_value = True
        mock_k10temp_loaded.return_value = True
        mock_priv.return_value = Mock(returncode=1)
        config = AMDConfig("fedora")

        result = config.setup_zenpower()

        assert result is False
        assert "Failed to unload k10temp module" in caplog.text

    @patch("aps.hardware.amd.run_privileged")
    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_blacklisted")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_loaded")
    def test_setup_zenpower_blacklist_creation_fails(
        self,
        mock_k10temp_loaded: Mock,
        mock_blacklisted: Mock,
        mock_amd: Mock,
        mock_priv: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test setup fails when creating blacklist file fails."""
        caplog.set_level("ERROR")
        mock_amd.return_value = True
        mock_k10temp_loaded.return_value = False
        mock_blacklisted.return_value = False
        mock_priv.return_value = Mock(returncode=1)
        config = AMDConfig("fedora")

        result = config.setup_zenpower()

        assert result is False
        assert "Failed to create blacklist file" in caplog.text

    @patch("aps.hardware.amd.AMDConfig._load_zenpower_module")
    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_blacklisted")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_loaded")
    def test_setup_zenpower_already_blacklisted(
        self,
        mock_k10temp_loaded: Mock,
        mock_blacklisted: Mock,
        mock_amd: Mock,
        mock_load: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test setup when k10temp is already blacklisted."""
        caplog.set_level("DEBUG")
        mock_amd.return_value = True
        mock_k10temp_loaded.return_value = False
        mock_blacklisted.return_value = True
        mock_load.return_value = True
        config = AMDConfig("fedora")

        result = config.setup_zenpower()

        assert result is True
        assert "k10temp is already blacklisted" in caplog.text


class TestAMDConfigLoadZenpower:
    """Test _load_zenpower_module method."""

    @patch("aps.hardware.amd.AMDConfig._is_zenpower_loaded")
    @patch("aps.hardware.amd.run_privileged")
    def test_load_zenpower_module_success(
        self, mock_priv: Mock, mock_loaded: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test successful loading of zenpower module."""
        caplog.set_level("INFO")
        mock_loaded.return_value = False
        mock_priv.return_value = Mock(returncode=0)
        config = AMDConfig("fedora")

        result = config._load_zenpower_module()  # type: ignore[attr-defined]

        assert result is True
        assert "zenpower module loaded successfully" in caplog.text

    @patch("aps.hardware.amd.AMDConfig._is_zenpower_loaded")
    @patch("aps.hardware.amd.run_privileged")
    def test_load_zenpower_module_failure(
        self, mock_priv: Mock, mock_loaded: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test failure to load zenpower module."""
        caplog.set_level("INFO")
        mock_loaded.return_value = False
        mock_priv.return_value = Mock(returncode=1)
        config = AMDConfig("fedora")

        result = config._load_zenpower_module()  # type: ignore[attr-defined]

        assert result is False
        assert "Failed to load zenpower module" in caplog.text
        assert "A system restart may be required" in caplog.text

    @patch("aps.hardware.amd.AMDConfig._is_zenpower_loaded")
    def test_load_zenpower_module_already_loaded(
        self, mock_loaded: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test when zenpower module is already loaded."""
        caplog.set_level("INFO")
        mock_loaded.return_value = True
        config = AMDConfig("fedora")

        result = config._load_zenpower_module()  # type: ignore[attr-defined]

        assert result is True
        assert "zenpower module is already loaded" in caplog.text


class TestAMDConfigConfigure:
    """Test configure method."""

    @patch("aps.hardware.amd.AMDConfig.setup_zenpower")
    def test_configure_calls_setup_zenpower(self, mock_setup: Mock) -> None:
        """Test configure method calls setup_zenpower."""
        mock_setup.return_value = True
        config = AMDConfig("fedora")

        result = config.configure(zenpower=True)

        assert result is True
        mock_setup.assert_called_once()

    def test_configure_no_zenpower(self) -> None:
        """Test configure method with no zenpower."""
        config = AMDConfig("fedora")

        result = config.configure()

        assert result is True
