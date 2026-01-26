"""Tests for multimedia configuration module."""

from unittest.mock import Mock, patch

from aps.system import multimedia


class TestMultimediaConfig:
    """Tests for multimedia configuration."""

    @patch("aps.system.multimedia.run_privileged")
    def test_configure_non_fedora(self, mock_run: Mock) -> None:
        """Test multimedia config on non-Fedora (should skip)."""
        result = multimedia.configure(distro="arch")

        assert result is True
        mock_run.assert_not_called()

    @patch("aps.system.multimedia.run_privileged")
    def test_configure_fedora_no_ffmpeg_free(self, mock_run: Mock) -> None:
        """Test multimedia config when ffmpeg-free not installed."""
        mock_run.return_value = Mock(returncode=1)  # Not installed

        result = multimedia.configure(distro="fedora")

        assert result is True

    @patch("aps.system.multimedia.run_privileged")
    def test_configure_fedora_ffmpeg_free_installed_swap_success(
        self, mock_run: Mock
    ) -> None:
        """Test multimedia config when ffmpeg-free installed, swap succeeds."""
        # First call: list installed, returncode=0 (installed)
        # Second call: swap, returncode=0 (success)
        mock_run.side_effect = [
            Mock(returncode=0),
            Mock(returncode=0),
        ]

        result = multimedia.configure(distro="fedora")

        assert result is True

    @patch("aps.system.multimedia.run_privileged")
    def test_configure_fedora_ffmpeg_free_installed_swap_failure(
        self, mock_run: Mock
    ) -> None:
        """Test multimedia config when ffmpeg-free installed but swap fails."""
        # First call: list installed, returncode=0 (installed)
        # Second call: swap, returncode=1 (failure)
        mock_run.side_effect = [
            Mock(returncode=0),
            Mock(returncode=1),
        ]

        result = multimedia.configure(distro="fedora")

        assert result is False
