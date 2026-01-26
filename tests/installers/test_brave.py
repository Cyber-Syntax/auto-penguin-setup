"""Tests for Brave browser installer module."""

from unittest.mock import patch

from aps.installers import brave


class TestBraveInstaller:
    """Tests for Brave Browser installer."""

    def test_is_installed_when_brave_exists(self) -> None:
        """Test _is_installed returns True when brave command exists."""
        with patch(
            "aps.installers.brave.shutil.which", return_value="/usr/bin/brave"
        ):
            assert brave._is_installed() is True

    def test_is_installed_when_brave_not_exists(self) -> None:
        """Test _is_installed returns False when brave command doesn't exist."""
        with patch("aps.installers.brave.shutil.which", return_value=None):
            assert brave._is_installed() is False

    def test_install_already_installed(self) -> None:
        """Test install when Brave is already installed."""
        with (
            patch("aps.installers.brave._is_installed", return_value=True),
            patch("aps.installers.brave._disable_keyring", return_value=True),
        ):
            result = brave.install()

        assert result is True

    def test_install_curl_not_available(self) -> None:
        """Test install fails when curl is not available."""
        with (
            patch("aps.installers.brave._is_installed", return_value=False),
            patch("aps.installers.brave.shutil.which", return_value=None),
        ):
            result = brave.install()

        assert result is False

    def test_install_success(self) -> None:
        """Test successful Brave installation."""
        with (
            patch("aps.installers.brave._is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch("aps.installers.brave._install_brave", return_value=True),
            patch("aps.installers.brave._disable_keyring", return_value=True),
        ):
            result = brave.install()

        assert result is True

    def test_install_brave_fail(self) -> None:
        """Test install fails when _install_brave fails."""
        with (
            patch("aps.installers.brave._is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch("aps.installers.brave._install_brave", return_value=False),
        ):
            result = brave.install()

        assert result is False

    def test_install_arch_success(self) -> None:
        """Test successful Brave installation on Arch."""
        with (
            patch("aps.installers.brave._is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch("aps.installers.brave._install_brave", return_value=True),
            patch("aps.installers.brave._disable_keyring", return_value=True),
        ):
            result = brave.install()

        assert result is True

    def test_install_disable_keyring_fail(self) -> None:
        """Test install succeeds but warns when _disable_keyring fails."""
        with (
            patch("aps.installers.brave._is_installed", return_value=False),
            patch(
                "aps.installers.brave.shutil.which",
                return_value="/usr/bin/curl",
            ),
            patch("aps.installers.brave._install_brave", return_value=True),
            patch("aps.installers.brave._disable_keyring", return_value=False),
        ):
            result = brave.install()

        assert result is True
