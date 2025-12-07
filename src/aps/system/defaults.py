"""Default application configuration using mimeapps.list."""

import logging
from datetime import datetime
from pathlib import Path

from .base import BaseSystemConfig

logger = logging.getLogger(__name__)


class DefaultAppsConfig(BaseSystemConfig):
    """Configure default applications via mimeapps.list."""

    # MIME type mappings
    BROWSER_MIMES = [
        "text/html",
        "text/xml",
        "application/xhtml+xml",
        "application/xml",
        "application/rss+xml",
        "application/rdf+xml",
        "x-scheme-handler/http",
        "x-scheme-handler/https",
        "x-scheme-handler/about",
        "x-scheme-handler/unknown",
    ]

    IMAGE_VIEWER_MIMES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/tiff",
        "image/svg+xml",
    ]

    TEXT_EDITOR_MIMES = [
        "text/plain",
        "text/x-python",
        "text/x-c",
        "text/x-c++",
        "text/x-java",
        "text/x-shellscript",
        "application/x-shellscript",
        "text/markdown",
        "text/x-markdown",
    ]

    FILE_MANAGER_MIMES = [
        "inode/directory",
    ]

    # Common application name to desktop file mappings
    APP_MAPPINGS = {
        "brave": "brave-browser.desktop",
        "chrome": "google-chrome.desktop",
        "google-chrome": "google-chrome.desktop",
        "firefox": "firefox.desktop",
        "firefox-esr": "firefox-esr.desktop",
        "librewolf": "librewolf.desktop",
        "chromium": "chromium-browser.desktop",
        "vscode": "code.desktop",
        "code": "code.desktop",
        "obsidian": "obsidian.desktop",
        "nautilus": "nautilus.desktop",
        "thunar": "thunar.desktop",
        "dolphin": "dolphin.desktop",
        "pcmanfm": "pcmanfm.desktop",
        "alacritty": "Alacritty.desktop",
        "kitty": "kitty.desktop",
        "gnome-terminal": "gnome-terminal.desktop",
        "konsole": "konsole.desktop",
        "feh": "feh.desktop",
        "sxiv": "sxiv.desktop",
        "gwenview": "gwenview.desktop",
        "eog": "eog.desktop",
        "vim": "vim.desktop",
        "nvim": "nvim.desktop",
        "gedit": "gedit.desktop",
        "kate": "kate.desktop",
    }

    def __init__(self) -> None:
        """Initialize default apps configuration."""
        super().__init__()
        self.config_dir = Path.home() / ".config"
        self.mimeapps_file = self.config_dir / "mimeapps.list"

    def configure(self) -> bool:
        """Configure default applications (placeholder implementation).

        This is a placeholder that returns True. The actual configuration
        should be done by calling set_defaults() with specific applications.

        Returns:
            bool: True (placeholder)
        """
        logger.info("Default applications configuration ready")
        logger.info("Use set_defaults() method to configure specific applications")
        return True

    def set_defaults(
        self,
        browser: str | None = None,
        terminal: str | None = None,
        file_manager: str | None = None,
        image_viewer: str | None = None,
        text_editor: str | None = None,
    ) -> bool:
        """Set default applications for various categories.

        Args:
            browser: Browser application name (e.g., 'brave', 'firefox')
            terminal: Terminal emulator name (e.g., 'alacritty', 'kitty')
            file_manager: File manager name (e.g., 'thunar', 'nautilus')
            image_viewer: Image viewer name (e.g., 'feh', 'eog')
            text_editor: Text editor name (e.g., 'nvim', 'gedit')

        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        logger.info("Setting up default applications with mimeapps.list...")

        # Create backup if file exists
        if self.mimeapps_file.exists():
            if not self._create_backup():
                logger.error("Failed to create backup of mimeapps.list")
                return False

        # Convert app names to desktop files
        apps = {}
        if browser:
            apps["browser"] = self._get_desktop_file(browser)
        if terminal:
            apps["terminal"] = self._get_desktop_file(terminal)
        if file_manager:
            apps["file_manager"] = self._get_desktop_file(file_manager)
        if image_viewer:
            apps["image_viewer"] = self._get_desktop_file(image_viewer)
        if text_editor:
            apps["text_editor"] = self._get_desktop_file(text_editor)

        # Generate mimeapps.list content
        content = self._generate_mimeapps_content(apps)

        # Write to file
        try:
            self.mimeapps_file.write_text(content)
            logger.info("Default applications configured successfully in %s", self.mimeapps_file)
            return True
        except (OSError, PermissionError) as e:
            logger.error("Failed to write mimeapps.list: %s", e)
            return False

    def _get_desktop_file(self, app_name: str) -> str:
        """Convert application name to desktop file name.

        Args:
            app_name: Application name

        Returns:
            str: Desktop file name
        """
        # Check if already a .desktop file
        if app_name.endswith(".desktop"):
            desktop_file = app_name
        # Check known mappings
        elif app_name in self.APP_MAPPINGS:
            desktop_file = self.APP_MAPPINGS[app_name]
        # Default to app_name + .desktop
        else:
            desktop_file = f"{app_name}.desktop"

        # Check if desktop file exists in standard locations
        search_paths = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path.home() / ".local/share/applications",
        ]

        found = any((path / desktop_file).exists() for path in search_paths)

        if not found:
            logger.warning(
                "Desktop file '%s' not found. The application may not be installed.",
                desktop_file,
            )

        logger.debug("Application '%s' mapped to desktop file: %s", app_name, desktop_file)
        return desktop_file

    def _generate_mimeapps_content(self, apps: dict[str, str]) -> str:
        """Generate mimeapps.list content.

        Args:
            apps: Dictionary of app categories to desktop files

        Returns:
            str: Content for mimeapps.list file
        """
        logger.debug("Generating mimeapps.list content...")

        # Build Default Applications section
        default_section = ["[Default Applications]"]

        browser = apps.get("browser")
        if browser:
            for mime in self.BROWSER_MIMES:
                default_section.append(f"{mime}={browser}")

        image_viewer = apps.get("image_viewer")
        if image_viewer:
            for mime in self.IMAGE_VIEWER_MIMES:
                default_section.append(f"{mime}={image_viewer}")

        text_editor = apps.get("text_editor")
        if text_editor:
            for mime in self.TEXT_EDITOR_MIMES:
                default_section.append(f"{mime}={text_editor}")

        file_manager = apps.get("file_manager")
        if file_manager:
            for mime in self.FILE_MANAGER_MIMES:
                default_section.append(f"{mime}={file_manager}")

        # Build Added Associations section (with semicolons)
        added_section = ["", "[Added Associations]"]

        if browser:
            for mime in self.BROWSER_MIMES:
                added_section.append(f"{mime}={browser};")

        if image_viewer:
            for mime in self.IMAGE_VIEWER_MIMES:
                added_section.append(f"{mime}={image_viewer};")

        if text_editor:
            for mime in self.TEXT_EDITOR_MIMES:
                added_section.append(f"{mime}={text_editor};")

        if file_manager:
            for mime in self.FILE_MANAGER_MIMES:
                added_section.append(f"{mime}={file_manager};")

        # Combine sections
        all_lines = default_section + added_section
        return "\n".join(all_lines) + "\n"

    def _create_backup(self) -> bool:
        """Create backup of mimeapps.list file.

        Returns:
            bool: True if backup was successful, False otherwise.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = self.mimeapps_file.with_suffix(f".list.bak.{timestamp}")

        logger.info("Creating backup of mimeapps.list...")

        try:
            import shutil

            shutil.copy2(self.mimeapps_file, backup_file)
            logger.info("Backup created: %s", backup_file)
            return True
        except (OSError, PermissionError) as e:
            logger.error("Failed to create backup: %s", e)
            return False
