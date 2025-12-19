"""Oh-My-Zsh installer with custom installation path."""

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from aps.core.logger import get_logger

from .base import BaseInstaller

logger = get_logger(__name__)


class OhMyZshInstaller(BaseInstaller):
    """Installer for Oh-My-Zsh with custom configuration path."""

    def install(self) -> bool:
        """Install Oh-My-Zsh and additional plugins.

        Returns:
            True if installation successful, False otherwise

        """
        logger.info("Installing oh-my-zsh...")

        target_dir = Path.home() / ".config" / "oh-my-zsh"
        default_dir = Path.home() / ".oh-my-zsh"

        # Precheck: ensure zsh binary exists so installer doesn't fail silently
        if shutil.which("zsh") is None:
            logger.error(
                "Zsh is not installed. Please install zsh first (e.g., 'sudo apt install zsh' or your distro equivalent)."
            )
            return False

        # Determine which zshrc file to use
        zshrc_path = self._get_zshrc_path()
        logger.info("Using zshrc at: %s", zshrc_path)

        # Check if already installed
        already_installed = target_dir.exists() or default_dir.exists()

        if already_installed:
            logger.info(
                "oh-my-zsh is already installed, updating configuration..."
            )
            # Ensure we're using the correct directory
            if default_dir.exists() and not target_dir.exists():
                logger.info(
                    "Moving oh-my-zsh from %s to %s", default_dir, target_dir
                )
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(default_dir), str(target_dir))
                except (OSError, shutil.Error) as e:
                    logger.error(
                        "Failed to move oh-my-zsh to target directory: %s", e
                    )
                    return False
        else:
            # Run official installer non-interactively, installing directly to target_dir
            installer_url = "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"

            install_env = os.environ.copy()
            install_env.update(
                {
                    "RUNZSH": "no",  # don't auto-start zsh after install
                    "CHSH": "no",  # don't change default shell
                    "KEEP_ZSHRC": "yes",
                    "ZSH": str(target_dir),  # install into desired path
                }
            )

            # Ensure target directory parent exists
            target_dir.parent.mkdir(parents=True, exist_ok=True)

            # Use sh -s -- to pass --unattended; capture both stdout and stderr
            cmd = f"wget -O- {installer_url} | sh -s -- --unattended"

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    env=install_env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.debug("Installer stdout: %s", result.stdout)
                if result.stderr:
                    logger.debug("Installer stderr: %s", result.stderr)
            except subprocess.CalledProcessError as e:
                combined_output = (
                    (e.stdout or "")
                    + ("\n" if e.stdout and e.stderr else "")
                    + (e.stderr or "")
                )
                logger.error(
                    "oh-my-zsh installation failed. Full output follows:\n%s",
                    combined_output.strip(),
                )
                return False

        # Ensure custom plugins directory exists
        zsh_custom = target_dir / "custom"
        plugins_dir = zsh_custom / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        # Install additional plugins
        self._install_plugin(
            "zsh-syntax-highlighting",
            "https://github.com/zsh-users/zsh-syntax-highlighting.git",
            plugins_dir,
        )

        self._install_plugin(
            "zsh-autosuggestions",
            "https://github.com/zsh-users/zsh-autosuggestions",
            plugins_dir,
        )

        # Fix path references in zshrc
        logger.info("Updating %s with correct paths...", zshrc_path)

        # Create backup
        backup_path = Path(
            f"{zshrc_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        try:
            shutil.copy2(zshrc_path, backup_path)
            logger.debug("Created backup at %s", backup_path)
        except (OSError, shutil.Error) as e:
            logger.warning("Failed to create backup: %s", e)

        # Update zshrc with correct paths
        if not self._update_zshrc(zshrc_path):
            logger.error("Failed to update zshrc configuration")
            return False

        logger.info("oh-my-zsh installation completed successfully!")
        logger.info("Installation directory: %s", target_dir)
        logger.info("Configuration file: %s", zshrc_path)
        logger.info("")
        logger.info("Please restart your shell or run: source %s", zshrc_path)

        return True

    def _get_zshrc_path(self) -> Path:
        """Determine which zshrc file to use.

        Returns:
            Path to zshrc file

        """
        config_zshrc = Path.home() / ".config" / "zsh" / ".zshrc"
        home_zshrc = Path.home() / ".zshrc"

        if config_zshrc.exists():
            return config_zshrc
        if home_zshrc.exists():
            return home_zshrc

        # Create preferred location
        config_zshrc.parent.mkdir(parents=True, exist_ok=True)
        config_zshrc.touch()
        return config_zshrc

    def _install_plugin(self, name: str, url: str, plugins_dir: Path) -> None:
        """Install a zsh plugin.

        Args:
            name: Plugin name
            url: Git repository URL
            plugins_dir: Plugins directory path

        """
        plugin_path = plugins_dir / name

        if not plugin_path.exists():
            logger.info("Installing %s plugin...", name)
            try:
                subprocess.run(
                    ["git", "clone", url, str(plugin_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.debug("Installed plugin: %s", name)
            except subprocess.CalledProcessError as e:
                logger.warning("Failed to install %s: %s", name, e.stderr)
        else:
            logger.debug("Plugin already installed: %s", name)

    def _update_zshrc(self, zshrc_path: Path) -> bool:
        """Update zshrc file with correct paths.

        Args:
            zshrc_path: Path to zshrc file

        Returns:
            True if successful, False otherwise

        """
        try:
            content = zshrc_path.read_text()
        except OSError as e:
            logger.error("Failed to read zshrc: %s", e)
            return False

        # Remove existing export ZSH lines
        content = re.sub(
            r"^\s*export ZSH=.*$", "", content, flags=re.MULTILINE
        )

        # Add correct export ZSH at the beginning
        content = 'export ZSH="$HOME/.config/oh-my-zsh"\n' + content

        # Replace path references
        content = content.replace(
            "$HOME/.oh-my-zsh", "$HOME/.config/oh-my-zsh"
        )
        content = content.replace("~/.oh-my-zsh", "$HOME/.config/oh-my-zsh")

        # Replace hardcoded absolute paths
        content = re.sub(
            r"/home/[^/]*/\.oh-my-zsh", "$HOME/.config/oh-my-zsh", content
        )

        # Ensure source line uses $ZSH variable
        content = re.sub(
            r"source [^\s]*/oh-my-zsh\.sh", "source $ZSH/oh-my-zsh.sh", content
        )

        # Write updated content
        try:
            zshrc_path.write_text(content)
        except OSError as e:
            logger.error("Failed to write zshrc: %s", e)
            return False

        # Verify critical lines exist
        if "export ZSH=" not in content:
            logger.warning("export ZSH line may not have been added correctly")

        if "oh-my-zsh.sh" not in content:
            logger.warning("oh-my-zsh.sh source line not found in zshrc")

        return True

    def is_installed(self) -> bool:
        """Check if oh-my-zsh is installed.

        Returns:
            True if installed, False otherwise

        """
        target_dir = Path.home() / ".config" / "oh-my-zsh"
        default_dir = Path.home() / ".oh-my-zsh"

        return target_dir.exists() or default_dir.exists()
