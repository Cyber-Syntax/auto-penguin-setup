"""Tests for NVIDIA GPU configuration module."""

from unittest.mock import Mock, patch

from pytest import LogCaptureFixture

from aps.hardware.nvidia import NvidiaConfig


class TestNvidiaConfigInit:
    """Test NvidiaConfig initialization."""

    def test_init_fedora(self) -> None:
        """Test initialization with fedora distro."""
        config = NvidiaConfig("fedora")
        assert config.distro == "fedora"

    def test_init_arch(self) -> None:
        """Test initialization with arch distro."""
        config = NvidiaConfig("arch")
        assert config.distro == "arch"


class TestNvidiaConfigDetection:
    """Test NVIDIA GPU detection."""

    @patch("subprocess.run")
    def test_has_nvidia_gpu_true(self, mock_run: Mock) -> None:
        """Test NVIDIA GPU detection when GPU is present."""
        mock_run.return_value = Mock(
            stdout="NVIDIA Corporation GP104 [GeForce RTX 2070]\n"
        )
        config = NvidiaConfig("fedora")

        result = config._has_nvidia_gpu()  # type: ignore[attr-defined]

        assert result is True

    @patch("subprocess.run")
    def test_has_nvidia_gpu_false(self, mock_run: Mock) -> None:
        """Test NVIDIA GPU detection when GPU is not present."""
        mock_run.return_value = Mock(
            stdout="Intel Corporation UHD Graphics 630\n"
        )
        config = NvidiaConfig("fedora")

        result = config._has_nvidia_gpu()  # type: ignore[attr-defined]

        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_has_nvidia_gpu_lspci_not_found(
        self, mock_run: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test NVIDIA GPU detection when lspci is not found."""
        caplog.set_level("WARNING")
        config = NvidiaConfig("fedora")

        result = config._has_nvidia_gpu()  # type: ignore[attr-defined]

        assert result is False
        assert "lspci command not found" in caplog.text


class TestNvidiaConfigSetupCuda:
    """Test CUDA setup functionality."""

    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_cuda_no_gpu(
        self, mock_gpu: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test setup fails when no NVIDIA GPU is found."""
        caplog.set_level("ERROR")
        mock_gpu.return_value = False
        config = NvidiaConfig("fedora")

        result = config.setup_cuda()

        assert result is False
        assert "No NVIDIA GPU detected" in caplog.text

    @patch("aps.hardware.nvidia.NvidiaConfig._setup_cuda_fedora")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_cuda_fedora(self, mock_gpu: Mock, mock_setup: Mock) -> None:
        """Test CUDA setup on Fedora."""
        mock_gpu.return_value = True
        mock_setup.return_value = True
        config = NvidiaConfig("fedora")

        result = config.setup_cuda()

        assert result is True
        mock_setup.assert_called_once()

    @patch("aps.hardware.nvidia.NvidiaConfig._setup_cuda_arch")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_cuda_arch(self, mock_gpu: Mock, mock_setup: Mock) -> None:
        """Test CUDA setup on Arch."""
        mock_gpu.return_value = True
        mock_setup.return_value = True
        config = NvidiaConfig("arch")

        result = config.setup_cuda()

        assert result is True
        mock_setup.assert_called_once()

    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_cuda_unsupported_distro(
        self, mock_gpu: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test setup fails with unsupported distribution."""
        caplog.set_level("ERROR")
        mock_gpu.return_value = True
        config = NvidiaConfig("unsupported")

        result = config.setup_cuda()

        assert result is False
        assert "Unsupported distribution" in caplog.text


class TestNvidiaConfigSetupCudaDetailed:
    """Test detailed CUDA setup methods."""

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_cuda_fedora_detailed(
        self,
        mock_gpu: Mock,
        mock_file: Mock,
        mock_run: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test detailed CUDA setup on Fedora with subprocess calls."""
        caplog.set_level("INFO")
        mock_gpu.return_value = True
        mock_run.side_effect = [
            Mock(returncode=0),  # dnf config-manager --add-repo
            Mock(returncode=0),  # dnf clean all
            Mock(returncode=0),  # dnf module disable
            Mock(returncode=0),  # dnf config-manager --set-enabled
            Mock(returncode=0),  # dnf install
            # nvcc --version
            Mock(returncode=0, stdout="nvcc: NVIDIA (R) Cuda compiler\n"),
        ]

        config = NvidiaConfig("fedora")
        result = config.setup_cuda()

        assert result is True

    @patch("subprocess.run")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_cuda_arch_detailed(
        self, mock_gpu: Mock, mock_run: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test detailed CUDA setup on Arch with subprocess calls."""
        caplog.set_level("INFO")
        mock_gpu.return_value = True
        mock_run.side_effect = [
            Mock(returncode=0),  # pacman -S
            # nvcc --version
            Mock(returncode=0, stdout="nvcc: NVIDIA (R) Cuda compiler\n"),
        ]

        config = NvidiaConfig("arch")
        result = config.setup_cuda()

        assert result is True


class TestNvidiaConfigSwitchToOpenDriver:
    """Test switch_to_open_driver functionality."""

    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_switch_to_open_driver_no_gpu(
        self, mock_gpu: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test switch fails when no GPU detected."""
        caplog.set_level("ERROR")
        mock_gpu.return_value = False
        config = NvidiaConfig("fedora")

        result = config.switch_to_open_driver()

        assert result is False
        assert "No NVIDIA GPU detected" in caplog.text

    @patch("os.geteuid")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_switch_to_open_driver_no_root(
        self, mock_gpu: Mock, mock_geteuid: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test switch fails without root privileges."""
        caplog.set_level("ERROR")
        mock_gpu.return_value = True
        mock_geteuid.return_value = 1000  # Non-root user

        config = NvidiaConfig("fedora")
        result = config.switch_to_open_driver()

        assert result is False
        assert "must be run as root" in caplog.text

    @patch("subprocess.run")
    @patch("os.uname")
    @patch("builtins.open")
    @patch("os.geteuid")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_switch_to_open_driver_fedora(
        self,
        mock_gpu: Mock,
        mock_geteuid: Mock,
        mock_file: Mock,
        mock_uname: Mock,
        mock_run: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test switch to open driver on Fedora."""
        caplog.set_level("INFO")
        mock_gpu.return_value = True
        mock_geteuid.return_value = 0  # Root user
        mock_uname.return_value = Mock(release="6.5.0")
        mock_run.side_effect = [
            Mock(returncode=0),  # akmods rebuild
            Mock(returncode=0),  # dnf --disablerepo
        ]

        config = NvidiaConfig("fedora")
        result = config.switch_to_open_driver()

        assert result is True
        assert "open source driver setup completed" in caplog.text


class TestNvidiaConfigSetupVaapi:
    """Test setup_vaapi functionality."""

    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_vaapi_no_gpu(
        self, mock_gpu: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test VA-API setup fails when no GPU detected."""
        caplog.set_level("ERROR")
        mock_gpu.return_value = False
        config = NvidiaConfig("fedora")

        result = config.setup_vaapi()

        assert result is False
        assert "No NVIDIA GPU detected" in caplog.text

    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_vaapi_non_fedora(
        self, mock_gpu: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test VA-API setup fails on non-Fedora distributions."""
        caplog.set_level("ERROR")
        mock_gpu.return_value = True
        config = NvidiaConfig("arch")

        result = config.setup_vaapi()

        assert result is False
        assert "only supported on Fedora" in caplog.text

    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("aps.hardware.nvidia.NvidiaConfig._has_nvidia_gpu")
    def test_setup_vaapi_fedora_success(
        self,
        mock_gpu: Mock,
        mock_file: Mock,
        mock_exists: Mock,
        mock_run: Mock,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test successful VA-API setup on Fedora."""
        caplog.set_level("INFO")
        mock_gpu.return_value = True
        mock_exists.return_value = False  # env file doesn't exist
        mock_run.return_value = Mock(returncode=0)  # dnf install

        config = NvidiaConfig("fedora")
        result = config.setup_vaapi()

        assert result is True
        assert "VA-API setup completed" in caplog.text


class TestNvidiaConfigConfigure:
    """Test configure method."""

    @patch("aps.hardware.nvidia.NvidiaConfig.setup_cuda")
    def test_configure_cuda(self, mock_setup: Mock) -> None:
        """Test configure method calls setup_cuda for cuda option."""
        mock_setup.return_value = True
        config = NvidiaConfig("fedora")

        result = config.configure(cuda=True)

        assert result is True
        mock_setup.assert_called_once()

    @patch("aps.hardware.nvidia.NvidiaConfig.setup_vaapi")
    def test_configure_vaapi(self, mock_setup: Mock) -> None:
        """Test configure method calls setup_vaapi for vaapi option."""
        mock_setup.return_value = True
        config = NvidiaConfig("fedora")

        result = config.configure(vaapi=True)

        assert result is True
        mock_setup.assert_called_once()

    @patch("aps.hardware.nvidia.NvidiaConfig.switch_to_open_driver")
    def test_configure_open_driver(self, mock_switch: Mock) -> None:
        """Test configure method calls switch_to_open_driver."""
        mock_switch.return_value = True
        config = NvidiaConfig("fedora")

        result = config.configure(open_driver=True)

        assert result is True
        mock_switch.assert_called_once()
