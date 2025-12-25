"""Oh-My-Zsh installer with custom installation path."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from aps.core.logger import get_logger

logger = get_logger(__name__)


def install(distro: str | None = None) -> bool:  # noqa: ARG001
    """Install Oh-My-Zsh and additional plugins.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    if shutil.which("zsh") is None:
        logger.error("Zsh is not installed. Please install zsh first")
        return False

    target_dir = Path.home() / ".config" / "oh-my-zsh"
    zshrc_path = _get_zshrc_path()

    if target_dir.exists():
        logger.info("oh-my-zsh already installed, updating configuration")
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        install_env = os.environ.copy()
        install_env.update(
            {
                "RUNZSH": "no",
                "CHSH": "no",
                "KEEP_ZSHRC": "yes",
                "ZSH": str(target_dir),
            }
        )

        installer_url = (
            "https://raw.githubusercontent.com/"
            "ohmyzsh/ohmyzsh/master/tools/install.sh"
        )
        installer_script = target_dir.parent / "install.sh"

        try:
            # Download installer script
            subprocess.run(  # noqa: S603
                [
                    "/usr/bin/wget",
                    "-O",
                    str(installer_script),
                    installer_url,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Execute installer script
            subprocess.run(  # noqa: S603
                ["/bin/sh", str(installer_script), "--unattended"],
                env=install_env,
                check=True,
                capture_output=False,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            output = (e.stdout or "") + (e.stderr or "")
            logger.exception("oh-my-zsh installation failed: %s", output)
            installer_script.unlink(missing_ok=True)
            return False
        else:
            # Clean up installer script
            installer_script.unlink(missing_ok=True)

    plugins_dir = target_dir / "custom" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    _install_plugin(
        "zsh-syntax-highlighting",
        "https://github.com/zsh-users/zsh-syntax-highlighting.git",
        plugins_dir,
    )
    _install_plugin(
        "zsh-autosuggestions",
        "https://github.com/zsh-users/zsh-autosuggestions",
        plugins_dir,
    )

    if not _update_zshrc(zshrc_path):
        return False

    logger.info("oh-my-zsh installed at %s", target_dir)
    return True


def _get_zshrc_path() -> Path:
    """Determine which zshrc file to use.

    Returns:
        Path to zshrc file

    """
    config_zshrc = Path.home() / ".config" / "zsh" / ".zshrc"
    if config_zshrc.exists():
        return config_zshrc
    return Path.home() / ".zshrc"


def _install_plugin(name: str, url: str, plugins_dir: Path) -> None:
    """Install a zsh plugin.

    Args:
        name: Plugin name
        url: Git repository URL
        plugins_dir: Plugins directory path

    """
    plugin_path = plugins_dir / name
    if not plugin_path.exists():
        git_bin = shutil.which("git") or "/usr/bin/git"
        try:
            subprocess.run(  # noqa: S603
                [git_bin, "clone", url, str(plugin_path)],
                check=True,
                capture_output=False,
                text=True,
            )
        except subprocess.CalledProcessError:
            logger.exception("Failed to install %s", name)


def _update_zshrc(zshrc_path: Path) -> bool:
    """Update zshrc file with correct paths.

    Args:
        zshrc_path: Path to zshrc file

    Returns:
        True if successful, False otherwise

    """
    try:
        content = zshrc_path.read_text()
        content = re.sub(
            r"^\s*export ZSH=.*$", "", content, flags=re.MULTILINE
        )
        content = 'export ZSH="$HOME/.config/oh-my-zsh"\n' + content
        content = re.sub(
            r"(\$HOME/)?~?/?\.oh-my-zsh|/home/[^/]*/\.oh-my-zsh",
            "$HOME/.config/oh-my-zsh",
            content,
        )
        content = re.sub(
            r"source [^\s]*/oh-my-zsh\.sh",
            "source $ZSH/oh-my-zsh.sh",
            content,
        )
        zshrc_path.write_text(content)
    except OSError:
        logger.exception("Failed to update zshrc")
        return False
    else:
        return True


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if oh-my-zsh is installed.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installed, False otherwise

    """
    return (Path.home() / ".config" / "oh-my-zsh").exists()
