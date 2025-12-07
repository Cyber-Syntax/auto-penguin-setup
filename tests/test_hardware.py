"""Tests for hardware configuration modules."""

from unittest.mock import MagicMock, mock_open, patch

from aps.hardware.amd import AMDConfig
from aps.hardware.hostname import HostnameConfig
from aps.hardware.intel import IntelConfig
from aps.hardware.nvidia import NvidiaConfig
from aps.hardware.touchpad import TouchpadConfig


class TestNvidiaConfig:
    """Tests for NvidiaConfig class."""

    @patch("subprocess.run")
    def test_has_nvidia_gpu_detected(self, mock_run):
        """Test NVIDIA GPU detection when GPU is present."""
        mock_run.return_value = MagicMock(stdout="NVIDIA Corporation GPU", returncode=0)
        config = NvidiaConfig("fedora")
        assert config._has_nvidia_gpu() is True

    @patch("subprocess.run")
    def test_has_nvidia_gpu_not_detected(self, mock_run):
        """Test NVIDIA GPU detection when GPU is absent."""
        mock_run.return_value = MagicMock(stdout="Intel GPU", returncode=0)
        config = NvidiaConfig("fedora")
        assert config._has_nvidia_gpu() is False

    @patch("subprocess.run")
    def test_setup_cuda_no_gpu(self, mock_run):
        """Test CUDA setup fails when no GPU detected."""
        mock_run.return_value = MagicMock(stdout="Intel GPU", returncode=0)
        config = NvidiaConfig("fedora")
        assert config.setup_cuda() is False

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="Fedora release 39")
    def test_setup_cuda_fedora_success(self, mock_file, mock_run):
        """Test CUDA setup on Fedora."""
        # Mock GPU detection
        mock_run.side_effect = [
            MagicMock(stdout="NVIDIA Corporation", returncode=0),  # GPU detection
            MagicMock(returncode=0),  # dnf addrepo
            MagicMock(returncode=0),  # dnf clean
            MagicMock(returncode=0),  # dnf module disable
            MagicMock(returncode=0),  # dnf config-manager setopt
            MagicMock(returncode=0),  # dnf install
            MagicMock(returncode=0),  # nvcc --version
        ]

        config = NvidiaConfig("fedora")
        assert config.setup_cuda() is True

    @patch("subprocess.run")
    def test_setup_cuda_arch_success(self, mock_run):
        """Test CUDA setup on Arch."""
        mock_run.side_effect = [
            MagicMock(stdout="NVIDIA Corporation", returncode=0),  # GPU detection
            MagicMock(returncode=0),  # pacman install
            MagicMock(returncode=0),  # nvcc --version
        ]

        config = NvidiaConfig("arch")
        assert config.setup_cuda() is True

    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_setup_cuda_debian_success(self, mock_exists, mock_run):
        """Test CUDA setup on Debian."""
        mock_exists.return_value = True  # Keyring already exists

        mock_run.side_effect = [
            MagicMock(stdout="NVIDIA Corporation", returncode=0),  # GPU detection
            MagicMock(returncode=0),  # apt install
            MagicMock(returncode=0),  # nvcc --version
        ]

        config = NvidiaConfig("debian")
        assert config.setup_cuda() is True

    @patch("subprocess.run")
    @patch("os.geteuid")
    def test_switch_to_open_driver_no_root(self, mock_geteuid, mock_run):
        """Test switching to open driver fails without root."""
        mock_run.return_value = MagicMock(stdout="NVIDIA Corporation", returncode=0)
        mock_geteuid.return_value = 1000  # Non-root user

        config = NvidiaConfig("fedora")
        assert config.switch_to_open_driver() is False

    @patch("subprocess.run")
    @patch("os.geteuid")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.uname")
    def test_switch_to_open_driver_fedora(self, mock_uname, mock_file, mock_geteuid, mock_run):
        """Test switching to open driver on Fedora."""
        mock_run.return_value = MagicMock(stdout="NVIDIA Corporation", returncode=0)
        mock_geteuid.return_value = 0  # Root user
        mock_uname.return_value = MagicMock(release="6.5.0")

        # Mock all subprocess calls
        mock_run.side_effect = [
            MagicMock(stdout="NVIDIA Corporation", returncode=0),  # GPU detection
            MagicMock(returncode=0),  # akmods rebuild
            MagicMock(returncode=0),  # dnf --disablerepo
        ]

        config = NvidiaConfig("fedora")
        assert config.switch_to_open_driver() is True

    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_setup_vaapi_fedora_success(self, mock_exists, mock_run):
        """Test VA-API setup on Fedora."""
        mock_exists.return_value = False  # env file doesn't exist

        mock_run.side_effect = [
            MagicMock(stdout="NVIDIA Corporation", returncode=0),  # GPU detection
            MagicMock(returncode=0),  # dnf install
        ]

        with patch("builtins.open", mock_open()):
            config = NvidiaConfig("fedora")
            assert config.setup_vaapi() is True

    @patch("subprocess.run")
    def test_setup_vaapi_non_fedora(self, mock_run):
        """Test VA-API setup fails on non-Fedora."""
        mock_run.return_value = MagicMock(stdout="NVIDIA Corporation", returncode=0)
        config = NvidiaConfig("arch")
        assert config.setup_vaapi() is False

    @patch("subprocess.run")
    def test_configure_cuda_option(self, mock_run):
        """Test configure method with cuda option."""
        mock_run.side_effect = [
            MagicMock(stdout="NVIDIA Corporation", returncode=0),  # GPU detection
            MagicMock(returncode=0),  # pacman install
            MagicMock(returncode=0),  # nvcc --version
        ]

        config = NvidiaConfig("arch")
        assert config.configure(cuda=True) is True


class TestAMDConfig:
    """Tests for AMDConfig class."""

    @patch("builtins.open", new_callable=mock_open, read_data="AMD Ryzen 5 5600X")
    def test_is_amd_cpu_detected(self, mock_file):
        """Test AMD CPU detection when CPU is present."""
        config = AMDConfig("fedora")
        assert config._is_amd_cpu() is True

    @patch("builtins.open", new_callable=mock_open, read_data="Intel Core i7")
    def test_is_amd_cpu_not_detected(self, mock_file):
        """Test AMD CPU detection when CPU is absent."""
        config = AMDConfig("fedora")
        assert config._is_amd_cpu() is False

    @patch("subprocess.run")
    def test_is_k10temp_loaded_true(self, mock_run):
        """Test k10temp module detection when loaded."""
        mock_run.return_value = MagicMock(stdout="k10temp 16384 0", returncode=0)
        config = AMDConfig("fedora")
        assert config._is_k10temp_loaded() is True

    @patch("subprocess.run")
    def test_is_k10temp_loaded_false(self, mock_run):
        """Test k10temp module detection when not loaded."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        config = AMDConfig("fedora")
        assert config._is_k10temp_loaded() is False

    @patch("builtins.open", new_callable=mock_open, read_data="Intel Core")
    def test_setup_zenpower_no_amd_cpu(self, mock_file):
        """Test zenpower setup fails on non-AMD CPU."""
        config = AMDConfig("fedora")
        assert config.setup_zenpower() is False

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="AMD Ryzen")
    def test_setup_zenpower_fedora_success(self, mock_file, mock_run):
        """Test zenpower setup on Fedora."""
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # lsmod (k10temp not loaded)
            MagicMock(returncode=0),  # dnf copr enable
            MagicMock(returncode=0),  # dnf install
            MagicMock(returncode=0),  # modprobe zenpower3
        ]

        config = AMDConfig("fedora")
        assert config.setup_zenpower() is True

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="AMD Ryzen")
    def test_setup_zenpower_arch_success(self, mock_file, mock_run):
        """Test zenpower setup on Arch."""
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # lsmod
            MagicMock(stdout="/usr/bin/paru", returncode=0),  # which paru
            MagicMock(returncode=0),  # paru -S zenpower3-dkms
            MagicMock(returncode=0),  # paru -S zenmonitor3
            MagicMock(returncode=0),  # modprobe zenpower3
        ]

        config = AMDConfig("arch")
        assert config.setup_zenpower() is True

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="AMD Ryzen")
    def test_setup_zenpower_arch_no_aur_helper(self, mock_file, mock_run):
        """Test zenpower setup fails on Arch without AUR helper."""
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # lsmod
            MagicMock(returncode=1),  # which paru
            MagicMock(returncode=1),  # which yay
        ]

        config = AMDConfig("arch")
        assert config.setup_zenpower() is False

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="AMD Ryzen")
    def test_setup_zenpower_debian_unsupported(self, mock_file, mock_run):
        """Test zenpower setup fails on Debian (unsupported)."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)  # lsmod

        config = AMDConfig("debian")
        assert config.setup_zenpower() is False

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="AMD Ryzen")
    def test_configure_zenpower_option(self, mock_file, mock_run):
        """Test configure method with zenpower option."""
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # lsmod
            MagicMock(returncode=0),  # dnf copr enable
            MagicMock(returncode=0),  # dnf install
            MagicMock(returncode=0),  # modprobe zenpower3
        ]

        config = AMDConfig("fedora")
        assert config.configure(zenpower=True) is True


class TestIntelConfig:
    """Tests for IntelConfig class."""

    @patch("os.path.exists")
    @patch("aps.hardware.base.BaseHardwareConfig._copy_config_file")
    def test_setup_xorg_success(self, mock_copy, mock_exists):
        """Test Xorg setup succeeds."""
        mock_exists.return_value = True
        mock_copy.return_value = True

        config = IntelConfig("fedora")
        assert config.setup_xorg() is True

    @patch("os.path.exists")
    def test_setup_xorg_file_not_found(self, mock_exists):
        """Test Xorg setup fails when config file not found."""
        mock_exists.return_value = False

        config = IntelConfig("fedora")
        assert config.setup_xorg() is False

    @patch("os.path.exists")
    @patch("aps.hardware.base.BaseHardwareConfig._copy_config_file")
    def test_setup_xorg_custom_source(self, mock_copy, mock_exists):
        """Test Xorg setup with custom config source."""
        mock_exists.return_value = True
        mock_copy.return_value = True

        config = IntelConfig("fedora")
        assert config.setup_xorg("/custom/path/intel.conf") is True

    @patch("os.path.exists")
    @patch("aps.hardware.base.BaseHardwareConfig._copy_config_file")
    def test_configure_xorg_option(self, mock_copy, mock_exists):
        """Test configure method with xorg option."""
        mock_exists.return_value = True
        mock_copy.return_value = True

        config = IntelConfig("fedora")
        assert config.configure(xorg=True) is True


class TestTouchpadConfig:
    """Tests for TouchpadConfig class."""

    @patch("os.path.exists")
    @patch("aps.hardware.base.BaseHardwareConfig._copy_config_file")
    def test_setup_success(self, mock_copy, mock_exists):
        """Test touchpad setup succeeds."""
        mock_exists.return_value = True
        mock_copy.return_value = True

        config = TouchpadConfig("fedora")
        assert config.setup() is True

    @patch("os.path.exists")
    def test_setup_file_not_found(self, mock_exists):
        """Test touchpad setup fails when config file not found."""
        mock_exists.return_value = False

        config = TouchpadConfig("fedora")
        assert config.setup() is False

    @patch("os.path.exists")
    @patch("aps.hardware.base.BaseHardwareConfig._copy_config_file")
    def test_setup_custom_source(self, mock_copy, mock_exists):
        """Test touchpad setup with custom config source."""
        mock_exists.return_value = True
        mock_copy.return_value = True

        config = TouchpadConfig("fedora")
        assert config.setup("/custom/path/touchpad.conf") is True

    @patch("os.path.exists")
    @patch("aps.hardware.base.BaseHardwareConfig._copy_config_file")
    def test_configure_setup_option(self, mock_copy, mock_exists):
        """Test configure method with setup option."""
        mock_exists.return_value = True
        mock_copy.return_value = True

        config = TouchpadConfig("fedora")
        assert config.configure(setup=True) is True


class TestHostnameConfig:
    """Tests for HostnameConfig class."""

    @patch("subprocess.run")
    def test_set_hostname_success(self, mock_run):
        """Test hostname setting succeeds."""
        mock_run.return_value = MagicMock(returncode=0)

        config = HostnameConfig("fedora")
        assert config.set_hostname("myhost") is True

    @patch("subprocess.run")
    def test_set_hostname_failure(self, mock_run):
        """Test hostname setting fails."""
        mock_run.return_value = MagicMock(returncode=1)

        config = HostnameConfig("fedora")
        assert config.set_hostname("myhost") is False

    def test_set_hostname_empty(self):
        """Test hostname setting fails with empty string."""
        config = HostnameConfig("fedora")
        assert config.set_hostname("") is False

    @patch("subprocess.run")
    def test_configure_hostname_option(self, mock_run):
        """Test configure method with hostname option."""
        mock_run.return_value = MagicMock(returncode=0)

        config = HostnameConfig("fedora")
        assert config.configure(hostname="myhost") is True

    def test_configure_no_hostname(self):
        """Test configure fails when no hostname provided."""
        config = HostnameConfig("fedora")
        assert config.configure() is False
