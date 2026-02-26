"""Virt-manager installer for virtualization management."""

import getpass
import re
import subprocess
from pathlib import Path

from aps.core.distro import DistroFamily, detect_distro
from aps.core.logger import get_logger
from aps.core.package_manager import PacmanManager, get_package_manager
from aps.utils.privilege import run_privileged

logger = get_logger(__name__)


def _arch_virtualization_packages(
    _pm: PacmanManager,
) -> list[str]:
    """Return simplified list of virtualization packages for Arch.

    Args:
        _pm: Package manager instance (unused, for consistency).

    Returns:
        List of package names to install.

    """
    return ["libvirt", "qemu-base", "virt-manager", "virt-install"]


def install(distro: str | None = None) -> bool:
    """Install virt-manager and configure virtualization.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installation successful, False otherwise

    """
    distro_info = detect_distro()

    # Prefer a canonical family key (arch/fedora) so derivatives like CachyOS
    # behave the same as their upstream family.
    if distro is None:
        if distro_info.family != DistroFamily.UNKNOWN:
            distro = distro_info.family.value
        else:
            distro = distro_info.id

    logger.info("Setting up virtualization...")

    if distro == "fedora":
        return _install_fedora()
    if distro == "arch":
        return _install_arch()
    logger.error("Unsupported distribution: %s", distro)
    return False


def _install_fedora() -> bool:
    """Install virtualization packages on Fedora."""
    logger.info("Installing virtualization packages for Fedora")

    # Fedora uses dnf groups for virtualization
    try:
        run_privileged(
            ["/usr/bin/dnf", "install", "-y", "@virtualization"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.exception("Failed to install virtualization group")
        return False

    # Install optional packages
    try:
        run_privileged(
            [
                "/usr/bin/dnf",
                "group",
                "install",
                "-y",
                "--with-optional",
                "virtualization",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except subprocess.SubprocessError:
        logger.warning("Failed to install optional virtualization packages")

    return _configure_libvirt()


def _install_arch() -> bool:
    """Install virtualization packages on Arch."""
    logger.info("Installing virtualization packages for Arch")

    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    if not isinstance(pm, PacmanManager):
        logger.error(
            "Expected PacmanManager for Arch-family distro, got %s",
            type(pm).__name__,
        )
        return False

    packages = _arch_virtualization_packages(pm)

    success, error = pm.install(packages, assume_yes=True)
    if not success:
        logger.error("Failed to install virtualization packages: %s", error)
        return False

    return _configure_libvirt()


def _setup_libvirt_group_access() -> bool:
    """Ensure libvirt group exists and add current user to it.

    Returns:
        True if group setup successful, False otherwise

    """
    # Ensure libvirt group exists
    try:
        result = subprocess.run(
            ["/usr/bin/getent", "group", "libvirt"],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.info("Creating libvirt group")
            run_privileged(
                ["/usr/sbin/groupadd", "libvirt"],
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError:
        logger.exception("Failed to create libvirt group")
        return False

    # Add current user to libvirt group
    try:
        username = getpass.getuser()
        run_privileged(
            ["/usr/sbin/usermod", "-aG", "libvirt", username],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Added user %s to libvirt group", username)
    except subprocess.CalledProcessError:
        logger.exception("Failed to add user to libvirt group")
        return False

    return True


def _configure_libvirt() -> bool:
    """Configure libvirt and add user to libvirt group.

    Integrates all non-root configuration steps:
    - Configures libvirtd.conf for socket access
    - Configures qemu.conf with user/group settings
    - Enables libvirtd.socket (socket mode per ArchWiki)
    - Configures network.conf for firewall settings
    """
    # Setup libvirt group access
    if not _setup_libvirt_group_access():
        return False

    # Configure libvirtd.conf for non-root access
    if not _configure_libvirtd_conf():
        logger.error("Failed to configure libvirtd.conf")
        return False

    # Configure qemu.conf for non-root access
    if not _configure_qemu_conf():
        logger.error("Failed to configure qemu.conf")
        return False

    # Enable and start libvirtd.socket (socket mode per ArchWiki)
    logger.info("Enabling libvirtd.socket...")
    try:
        run_privileged(
            ["/usr/bin/systemctl", "enable", "--now", "libvirtd.socket"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug("Enabled libvirtd.socket")
    except subprocess.CalledProcessError:
        logger.exception("Failed to enable libvirtd.socket")
        return False

    # Configure network.conf after socket is enabled
    if not _setup_network_config():
        logger.error("Failed to configure network.conf")
        return False

    logger.info("Virtualization setup completed successfully")
    logger.info(
        "Note: You may need to log out and back in for "
        "group changes to take effect"
    )

    return True


def _append_or_update_libvirt_setting(
    file_path: Path, key: str, value: str
) -> bool:
    """Append or update a setting in a libvirt config file.

    Args:
        file_path: Path to the libvirt config file.
        key: Setting key.
        value: Setting value.

    Returns:
        bool: True if setting was added/updated successfully, False otherwise.

    """
    try:
        # Read existing file content or create empty content for new files
        try:
            content = file_path.read_text()
        except FileNotFoundError:
            logger.debug("File does not exist, will create: %s", file_path)
            content = ""

        setting_line = f'{key} = "{value}"'

        # Check if key exists using regex pattern
        pattern = rf"^\s*{re.escape(key)}\s*=\s*(.+)$"
        match = re.search(pattern, content, re.MULTILINE)

        if match:
            current_value = match.group(1).strip().strip('"')
            if current_value == value:
                logger.debug("%s is already set to %s", key, value)
                return True

            # Update existing setting
            logger.debug(
                "Updating %s from %s to %s", key, current_value, value
            )
            new_content = re.sub(
                pattern, setting_line, content, flags=re.MULTILINE
            )

            result = run_privileged(
                ["/usr/bin/tee", str(file_path)],
                stdin_input=new_content,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error("Failed to update setting: %s", key)
                return False

            logger.info("Updated %s to %s", key, value)
            return True

        # Add new setting
        logger.debug("Adding setting: %s", setting_line)
        new_content = content.rstrip() + "\n" + setting_line + "\n"

        result = run_privileged(
            ["/usr/bin/tee", str(file_path)],
            stdin_input=new_content,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to add setting: %s", key)
            return False

        logger.info("Added %s = %s", key, value)
        return True  # noqa: TRY300

    except Exception:
        logger.exception("Error adding/updating setting %s", key)
        return False


def _create_backup(file_path: Path) -> bool:
    """Create backup of a file with .bak suffix.

    Args:
        file_path: Path to the file to backup.

    Returns:
        bool: True if backup was created or already exists, False on error.

    """
    backup_path = Path(f"{file_path}.bak")

    if backup_path.exists():
        logger.debug("Backup already exists: %s", backup_path)
        return True

    logger.debug("Creating backup of %s", file_path)

    result = run_privileged(
        ["/usr/bin/cp", str(file_path), str(backup_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.error("Failed to create backup of %s", file_path)
        return False

    logger.info("Backup created: %s", backup_path)
    return True


def _uncomment_line(file_path: Path, pattern: str) -> bool:
    """Uncomment a line matching the given pattern.

    Args:
        file_path: Path to the file.
        pattern: Pattern to match in a line (e.g., "unix_sock_group").

    Returns:
        bool: True on success, False on failure or pattern not found.

    """
    try:
        content = file_path.read_text()

        lines = content.split("\n")
        new_lines = []
        found = False
        for line in lines:
            if pattern in line:
                if line.lstrip().startswith("#"):
                    uncommented = line.lstrip()[1:].lstrip()
                    new_lines.append(uncommented)
                    found = True
                else:
                    new_lines.append(line)
                    found = True
            else:
                new_lines.append(line)

        if not found:
            logger.debug("Pattern not found in %s: %s", file_path, pattern)
            return False

        new_content = "\n".join(new_lines)

        if new_content == content:
            logger.debug("Line already uncommented: %s", pattern)
            return True

        result = run_privileged(
            ["/usr/bin/tee", str(file_path)],
            stdin_input=new_content,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to uncomment line in %s", file_path)
            return False
        logger.info("Uncommented line for pattern: %s", pattern)
        return True  # noqa: TRY300
    except Exception:
        logger.exception("Error uncommenting line in %s", file_path)
        return False


def _uncomment_and_replace(
    file_path: Path, pattern: str, old_value: str, new_value: str
) -> bool:
    """Uncomment and replace a value in a config file.

    Args:
        file_path: Path to the config file.
        pattern: Pattern to match (e.g., "user").
        old_value: Value to replace.
        new_value: New value to use.

    Returns:
        bool: True on success, False on failure or pattern not found.

    """
    try:
        content = file_path.read_text()

        # Pattern to find setting line (commented or uncommented, any value)
        # Use \s{0,1} instead of \s* to only match 0-1 spaces after #,
        # avoiding deeply indented examples like #       user = "qemu"
        find_pattern = rf'(^|\n)\s*#?\s{{0,1}}{re.escape(pattern)}\s*=\s*["\']?[^"\'\n]+["\']?'

        match = re.search(find_pattern, content, re.MULTILINE)

        if not match:
            logger.debug(
                "Pattern not found in %s: %s",
                file_path,
                pattern,
            )
            return False

        matched_line = match.group(0)

        # Check if the value is already correct
        if new_value in matched_line and old_value not in matched_line:
            logger.debug("Value already correct: %s = %s", pattern, new_value)
            return True

        new_line = f'{pattern} = "{new_value}"'

        new_content = re.sub(
            find_pattern,
            rf"\1{new_line}",
            content,
            count=1,
            flags=re.MULTILINE,
        )

        if new_content == content:
            logger.debug("Value already correct: %s = %s", pattern, new_value)
            return True

        result = run_privileged(
            ["/usr/bin/tee", str(file_path)],
            stdin_input=new_content,
            capture_output=True,
            text=True,
            check=False,
        )

        success = result.returncode == 0
        if not success:
            logger.error("Failed to update setting in %s", file_path)
        else:
            logger.info(
                "Updated %s to %s in %s", pattern, new_value, file_path
            )
        return success  # noqa: TRY300
    except Exception:
        logger.exception("Error updating %s in %s", pattern, file_path)
        return False


def is_installed(distro: str | None = None) -> bool:  # noqa: ARG001
    """Check if virt-manager is installed.

    Args:
        distro: Distribution name (optional, will auto-detect if None)

    Returns:
        True if installed, False otherwise

    """
    distro_info = detect_distro()
    pm = get_package_manager(distro_info)
    return pm.is_installed("virt-manager")


def _configure_libvirtd_conf() -> bool:
    """Configure libvirtd.conf for non-root access.

    Uncomments unix_sock_group and unix_sock_rw_perms settings to allow
    non-root users in the libvirt group to access the libvirt socket.

    Returns:
        True if configuration successful, False otherwise

    """
    libvirtd_conf = Path("/etc/libvirt/libvirtd.conf")

    logger.info("Configuring libvirtd.conf for non-root access...")

    # Create backup before making changes
    if not _create_backup(libvirtd_conf):
        logger.error("Failed to create backup of libvirtd.conf")
        return False

    # Uncomment unix_sock_group setting
    if not _uncomment_line(libvirtd_conf, "unix_sock_group"):
        logger.error("Failed to uncomment unix_sock_group")
        return False

    # Uncomment unix_sock_rw_perms setting
    if not _uncomment_line(libvirtd_conf, "unix_sock_rw_perms"):
        logger.error("Failed to uncomment unix_sock_rw_perms")
        return False

    logger.info("Successfully configured libvirtd.conf")
    return True


def _configure_qemu_conf() -> bool:
    """Configure qemu.conf for non-root access.

    Uncomments and sets user and group settings to the current username
    to allow non-root users to manage virtual machines.

    Returns:
        True if configuration successful, False otherwise

    """
    qemu_conf = Path("/etc/libvirt/qemu.conf")

    logger.info("Configuring qemu.conf for non-root access...")

    # Create backup before making changes
    if not _create_backup(qemu_conf):
        logger.error("Failed to create backup of qemu.conf")
        return False

    # Get current username
    username = getpass.getuser()

    # Uncomment and replace user setting
    if not _uncomment_and_replace(qemu_conf, "user", "libvirt-qemu", username):
        logger.error("Failed to configure user in qemu.conf")
        return False

    # Uncomment and replace group setting
    if not _uncomment_and_replace(
        qemu_conf, "group", "libvirt-qemu", username
    ):
        logger.error("Failed to configure group in qemu.conf")
        return False

    logger.info("Successfully configured qemu.conf")
    return True


def _setup_network_config() -> bool:
    """Configure network.conf for libvirt and set firewall backend.

    Creates backup and appends firewall_backend = "iptables" to
    /etc/libvirt/network.conf if not already present.

    Returns:
        True if configuration successful, False otherwise

    """
    network_conf = Path("/etc/libvirt/network.conf")

    logger.info("Configuring libvirt network.conf...")

    # Check if network.conf exists
    if not network_conf.exists():
        logger.error("Network configuration file not found: %s", network_conf)
        return False

    # Create backup before making changes
    if not _create_backup(network_conf):
        logger.error("Failed to create backup of network.conf")
        return False

    # Append or update firewall_backend setting
    if not _append_or_update_libvirt_setting(
        network_conf, "firewall_backend", "iptables"
    ):
        logger.error("Failed to configure firewall_backend in network.conf")
        return False

    logger.info("Successfully configured network.conf")
    return True
