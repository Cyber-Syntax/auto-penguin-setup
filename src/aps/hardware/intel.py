"""Intel graphics configuration."""

from pathlib import Path

from aps.core.logger import get_logger
from aps.utils.file_operations import copy_config_file
from aps.utils.paths import resolve_config_file

logger = get_logger(__name__)


def setup_xorg(config_source: str | None = None) -> bool:
    """Setup Xorg configuration for Intel graphics.

    Args:
        config_source: Path to Intel Xorg configuration file

    Returns:
        True if setup succeeds, False otherwise

    """
    if config_source is None:
        config_source = str(resolve_config_file("20-intel.conf"))

    logger.info("Setting up xorg configuration...")

    destination = "/etc/X11/xorg.conf.d/20-intel.conf"

    if not Path(config_source).exists():
        logger.error("Intel configuration file not found: %s", config_source)
        return False

    if copy_config_file(config_source, destination):
        logger.info("Xorg configuration completed.")
        return True

    return False


def configure(distro: str, **kwargs) -> bool:
    """Configure Intel hardware.

    Args:
        distro: Distribution name (fedora, arch) - not currently used
        **kwargs: Configuration options
            - xorg: bool - Setup Xorg configuration
            - config_source: str - Path to Intel config file

    Returns:
        True if all requested operations succeed

    """
    if kwargs.get("xorg", False):
        config_source = kwargs.get(
            "config_source", str(resolve_config_file("20-intel.conf"))
        )
        return setup_xorg(config_source)

    return True
