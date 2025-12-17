"""Tests for AMD CPU configuration module."""

from unittest.mock import Mock, patch

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

    def test_init_debian(self) -> None:
        """Test initialization with debian distro."""
        config = AMDConfig("debian")
        assert config.distro == "debian"


class TestAMDConfigDetection:
    """Test AMD CPU and module detection."""

    @patch("builtins.open", create=True)
    def test_is_amd_cpu_true(self, mock_open: Mock) -> None:
        """Test AMD CPU detection when AMD is present."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "AMD Ryzen 5000\n"
        )
        config = AMDConfig("fedora")

        result = config._is_amd_cpu()  # type: ignore[attr-defined]

        assert result is True

    @patch("builtins.open", create=True)
    def test_is_amd_cpu_false(self, mock_open: Mock) -> None:
        """Test AMD CPU detection when AMD is not present."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "Intel Core i7\n"
        )
        config = AMDConfig("fedora")

        result = config._is_amd_cpu()  # type: ignore[attr-defined]

        assert result is False

    @patch("builtins.open", side_effect=FileNotFoundError)
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
        mock_run.return_value = Mock(stdout="k10temp 16384 0\n")
        config = AMDConfig("fedora")

        result = config._is_k10temp_loaded()  # type: ignore[attr-defined]

        assert result is True
        mock_run.assert_called_once_with(
            ["lsmod"], capture_output=True, text=True, check=False
        )

    @patch("subprocess.run")
    def test_is_k10temp_loaded_false(self, mock_run: Mock) -> None:
        """Test k10temp module detection when not loaded."""
        mock_run.return_value = Mock(stdout="acpi_power_meter\n")
        config = AMDConfig("fedora")

        result = config._is_k10temp_loaded()  # type: ignore[attr-defined]

        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_is_k10temp_loaded_lsmod_not_found(self, mock_run: Mock) -> None:
        """Test k10temp detection when lsmod is not found."""
        config = AMDConfig("fedora")

        result = config._is_k10temp_loaded()  # type: ignore[attr-defined]

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
    @patch("builtins.open", create=True)
    @patch("aps.hardware.amd.AMDConfig._is_amd_cpu")
    @patch("aps.hardware.amd.AMDConfig._is_k10temp_loaded")
    @patch("aps.hardware.amd.AMDConfig._setup_zenpower_fedora")
    def test_setup_zenpower_fedora_success(
        self,
        mock_fedora: Mock,
        mock_k10temp: Mock,
        mock_amd: Mock,
        mock_open: Mock,
        mock_priv: Mock,
    ) -> None:
        """Test successful zenpower setup on Fedora."""
        mock_amd.return_value = True
        mock_k10temp.return_value = True
        mock_priv.return_value = Mock(returncode=0)
        mock_fedora.return_value = True
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
