"""Touchpad configuration."""

from pathlib import Path

from aps.core.logger import get_logger
from aps.utils.file_operations import copy_config_file
from aps.utils.paths import resolve_config_file

logger = get_logger(__name__)


def setup(config_source: str | None = None) -> bool:
    """Setup touchpad configuration.

    Args:
        config_source: Path to touchpad configuration file

    Returns:
        True if setup succeeds, False otherwise

    """
    if config_source is None:
        config_source = str(resolve_config_file("99-touchpad.conf"))

    logger.info("Setting up touchpad configuration...")

    destination = "/etc/X11/xorg.conf.d/99-touchpad.conf"

    if not Path(config_source).exists():
        logger.error("Touchpad configuration file not found: %s", config_source)
        return False

    if copy_config_file(config_source, destination):
        logger.info("Touchpad configuration completed.")
        return True

    return False


def configure(distro: str, **kwargs) -> bool:
    """Configure touchpad.

    Args:
        distro: Distribution name (fedora, arch) - not currently used
        **kwargs: Configuration options
            - setup: bool - Setup touchpad configuration
            - config_source: str - Path to touchpad config file

    Returns:
        True if all requested operations succeed

    """
    if kwargs.get("setup", False):
        config_source = kwargs.get(
            "config_source", str(resolve_config_file("99-touchpad.conf"))
        )
        return setup(config_source)

    return True
