"""Tests for installer base configuration module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture

from aps.installers.base import BaseInstaller


class ConcreteInstaller(BaseInstaller):
    """Concrete implementation of BaseInstaller for testing."""

    def install(self) -> bool:
        """Concrete implementation of install method."""
        return True


class TestBaseInstallerInit:
    """Test BaseInstaller initialization."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init_initializes_attributes(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test that __init__ properly initializes attributes."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_pm.return_value = MagicMock()

        installer = ConcreteInstaller()

        assert installer.distro == "fedora"
        assert installer.pm is not None
        mock_distro.assert_called_once()
        mock_pm.assert_called_once()

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init_with_arch(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization with arch distro."""
        mock_distro.return_value = MagicMock(id="arch")
        installer = ConcreteInstaller()
        assert installer.distro == "arch"

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_init_with_debian(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test initialization with debian distro."""
        mock_distro.return_value = MagicMock(id="debian")
        installer = ConcreteInstaller()
        assert installer.distro == "debian"


class TestBaseInstallerAbstractMethods:
    """Test abstract methods enforcement."""

    def test_cannot_instantiate_base_class(self) -> None:
        """Test that BaseInstaller cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseInstaller()  # type: ignore


class TestTryOfficialFirst:
    """Test try_official_first method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_try_official_first_when_available(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test trying official first when package is available."""
        caplog.set_level("INFO")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_package_manager = MagicMock()
        mock_package_manager.is_available_in_official_repos.return_value = True
        mock_package_manager.install.return_value = (True, None)
        mock_pm.return_value = mock_package_manager

        installer = ConcreteInstaller()
        fallback = Mock(return_value=False)

        result = installer.try_official_first("testpkg", fallback)

        assert result is True
        fallback.assert_not_called()
        assert "official repositories" in caplog.text

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_try_official_first_fallback_when_not_available(
        self, mock_pm: Mock, mock_distro: Mock
    ) -> None:
        """Test fallback when package not in official repos."""
        mock_distro.return_value = MagicMock(id="fedora")
        mock_package_manager = MagicMock()
        mock_package_manager.is_available_in_official_repos.return_value = False
        mock_pm.return_value = mock_package_manager

        installer = ConcreteInstaller()
        fallback = Mock(return_value=True)

        result = installer.try_official_first("testpkg", fallback)

        assert result is True
        fallback.assert_called_once()

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_try_official_first_fallback_on_install_failure(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test fallback when official install fails."""
        caplog.set_level("WARNING")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_package_manager = MagicMock()
        mock_package_manager.is_available_in_official_repos.return_value = True
        mock_package_manager.install.return_value = (False, "Install failed")
        mock_pm.return_value = mock_package_manager

        installer = ConcreteInstaller()
        fallback = Mock(return_value=True)

        result = installer.try_official_first("testpkg", fallback)

        assert result is True
        fallback.assert_called_once()
        assert "Failed to install from official repos" in caplog.text


class TestAddRepository:
    """Test add_repository method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_add_repository_without_gpg_key(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test adding repository without GPG key."""
        caplog.set_level("INFO")
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()
        installer._add_repo_file = Mock(return_value=True)

        result = installer.add_repository("https://example.com/repo", "example-repo")

        assert result is True
        installer._add_repo_file.assert_called_once()
        assert "Adding repository" in caplog.text

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_add_repository_with_gpg_key(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test adding repository with GPG key."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()
        installer._import_gpg_key = Mock(return_value=True)
        installer._add_repo_file = Mock(return_value=True)

        result = installer.add_repository(
            "https://example.com/repo", "example-repo", "https://example.com/key.gpg"
        )

        assert result is True
        installer._import_gpg_key.assert_called_once()
        installer._add_repo_file.assert_called_once()

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_add_repository_gpg_import_fails(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test failure when GPG key import fails."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()
        installer._import_gpg_key = Mock(return_value=False)

        result = installer.add_repository(
            "https://example.com/repo", "example-repo", "https://example.com/key.gpg"
        )

        assert result is False
        assert "Failed to import GPG key" in caplog.text


class TestImportGpgKey:
    """Test _import_gpg_key method."""

    @patch("aps.installers.base.run_privileged")
    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_import_gpg_key_fedora(
        self, mock_pm: Mock, mock_distro: Mock, mock_run_priv: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test GPG key import on Fedora."""
        caplog.set_level("DEBUG")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_result = MagicMock(returncode=0)
        mock_run_priv.return_value = mock_result

        installer = ConcreteInstaller()
        result = installer._import_gpg_key("https://example.com/key.gpg")

        assert result is True
        mock_run_priv.assert_called_once()
        call_args = mock_run_priv.call_args
        assert call_args[0][0][0] == "rpm"

    @patch("aps.installers.base.run_privileged")
    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_import_gpg_key_debian(
        self, mock_pm: Mock, mock_distro: Mock, mock_run_priv: Mock
    ) -> None:
        """Test GPG key import on Debian."""
        mock_distro.return_value = MagicMock(id="debian")
        mock_result = MagicMock(returncode=0)
        mock_run_priv.return_value = mock_result

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stdout="key content")

            installer = ConcreteInstaller()
            result = installer._import_gpg_key("https://example.com/key.gpg")

            assert result is True

    @patch("aps.installers.base.run_privileged")
    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_import_gpg_key_unsupported_distro(
        self, mock_pm: Mock, mock_distro: Mock, mock_run_priv: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test GPG key import on unsupported distro."""
        caplog.set_level("WARNING")
        mock_distro.return_value = MagicMock(id="unknown")
        installer = ConcreteInstaller()

        result = installer._import_gpg_key("https://example.com/key.gpg")

        assert result is True  # Continues anyway
        assert "not implemented" in caplog.text.lower()

    @patch("aps.installers.base.run_privileged")
    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_import_gpg_key_failure(
        self, mock_pm: Mock, mock_distro: Mock, mock_run_priv: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test GPG key import failure."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="fedora")
        mock_result = MagicMock(returncode=1)
        mock_run_priv.return_value = mock_result

        installer = ConcreteInstaller()
        result = installer._import_gpg_key("https://example.com/key.gpg")

        assert result is False


class TestAddRepoFile:
    """Test _add_repo_file method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_add_repo_file_fedora(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test adding repo file on Fedora."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()

        result = installer._add_repo_file("https://example.com/repo", "example")

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_add_repo_file_debian(self, mock_pm: Mock, mock_distro: Mock) -> None:
        """Test adding repo file on Debian."""
        mock_distro.return_value = MagicMock(id="debian")
        installer = ConcreteInstaller()

        result = installer._add_repo_file("https://example.com/repo", "example")

        assert result is True

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_add_repo_file_unsupported_distro(
        self, mock_pm: Mock, mock_distro: Mock, caplog: LogCaptureFixture
    ) -> None:
        """Test adding repo file on unsupported distro."""
        caplog.set_level("WARNING")
        mock_distro.return_value = MagicMock(id="unknown")
        installer = ConcreteInstaller()

        result = installer._add_repo_file("https://example.com/repo", "example")

        assert result is True  # Continues anyway
        assert "not implemented" in caplog.text.lower()


class TestCreateDesktopFile:
    """Test create_desktop_file method."""

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_create_desktop_file_simple(
        self, mock_pm: Mock, mock_distro: Mock, tmp_path: Path
    ) -> None:
        """Test creating desktop file without modifications."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()

        source = tmp_path / "source.desktop"
        source.write_text("[Desktop Entry]\nName=Test\n")

        user_path = tmp_path / "user"
        user_file = user_path / "test.desktop"

        result = installer.create_desktop_file(str(source), str(user_file))

        assert result is True
        assert user_file.exists()
        assert "Test" in user_file.read_text()

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_create_desktop_file_with_modifications(
        self, mock_pm: Mock, mock_distro: Mock, tmp_path: Path
    ) -> None:
        """Test creating desktop file with modifications."""
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()

        source = tmp_path / "source.desktop"
        source.write_text("[Desktop Entry]\nName=Test\nExec=test\n")

        user_path = tmp_path / "user"
        user_file = user_path / "test.desktop"

        modifications = {"Exec": "new-test"}
        result = installer.create_desktop_file(str(source), str(user_file), modifications)

        assert result is True
        content = user_file.read_text()
        assert "Exec=new-test" in content

    @patch("aps.installers.base.detect_distro")
    @patch("aps.installers.base.get_package_manager")
    def test_create_desktop_file_source_not_found(
        self, mock_pm: Mock, mock_distro: Mock, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test handling of missing source file."""
        caplog.set_level("ERROR")
        mock_distro.return_value = MagicMock(id="fedora")
        installer = ConcreteInstaller()

        source = tmp_path / "nonexistent.desktop"
        user_file = tmp_path / "user" / "test.desktop"

        result = installer.create_desktop_file(str(source), str(user_file))

        assert result is False
