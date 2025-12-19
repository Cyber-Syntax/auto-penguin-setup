"""SSH configuration and key management.

This module provides automated SSH setup including:
- Ed25519 key generation
- SSH daemon security configuration
- SSH key distribution to remote hosts
- SSH client configuration generation
"""

import logging
import re
import socket
import subprocess
from datetime import datetime
from pathlib import Path

from aps.system.base import BaseSystemConfig
from aps.utils.privilege import run_privileged

logger = logging.getLogger(__name__)


class SSHConfig(BaseSystemConfig):
    """SSH configuration and key management."""

    def __init__(self):
        """Initialize SSH configuration."""
        super().__init__()
        self.ssh_dir = Path.home() / ".ssh"
        self.key_path = self.ssh_dir / "id_ed25519"
        self.pub_key_path = self.ssh_dir / "id_ed25519.pub"
        self.config_file = self.ssh_dir / "config"

    def _get_ssh_service_name(self) -> str:
        """Get the SSH service name for the current distribution.

        Returns:
            Service name ("sshd" for Fedora/Arch, "ssh" for Debian)

        Raises:
            RuntimeError: If SSH service cannot be determined

        """
        distro = self.distro

        if distro in ["fedora", "arch"]:
            return "sshd"
        if distro == "debian":
            return "ssh"

        # Fallback detection
        result = subprocess.run(
            ["systemctl", "list-unit-files"],
            capture_output=True,
            text=True,
            check=False,
        )

        if "sshd.service" in result.stdout:
            return "sshd"
        if "ssh.service" in result.stdout:
            return "ssh"

        raise RuntimeError("Could not detect SSH service name")

    def _check_host_reachable(
        self, ip: str, port: int, timeout: int = 3
    ) -> bool:
        """Check if remote host is reachable on specified port.

        Args:
            ip: IP address to check
            port: Port number to check
            timeout: Connection timeout in seconds

        Returns:
            True if host is reachable, False otherwise

        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except (TimeoutError, OSError):
            return False

    def _parse_remote_host(self, host_string: str) -> tuple[str, str, int]:
        """Parse user@ip:port format into components.

        Args:
            host_string: String in format "user@ip:port"

        Returns:
            Tuple of (user, ip, port)

        Raises:
            ValueError: If format is invalid

        """
        pattern = r"^([^@]+)@([^:]+):([0-9]+)$"
        match = re.match(pattern, host_string)

        if not match:
            raise ValueError(
                f"Invalid host format: {host_string} (expected user@ip:port)"
            )

        user = match.group(1)
        ip = match.group(2)
        port = int(match.group(3))

        return user, ip, port

    def create_ssh_keys(self, force: bool = False) -> bool:
        """Create Ed25519 SSH keys if they don't exist.

        Args:
            force: If True, overwrite existing keys

        Returns:
            True if keys were created or already exist

        """
        if self.key_path.exists() and self.pub_key_path.exists() and not force:
            logger.debug("Ed25519 SSH keys already exist at %s", self.key_path)
            return True

        logger.info("Generating Ed25519 SSH keys...")

        # Create .ssh directory
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)

        # Generate Ed25519 key with no passphrase
        hostname = subprocess.run(
            ["hostname"], capture_output=True, text=True, check=True
        ).stdout.strip()

        result = subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-f",
                str(self.key_path),
                "-N",
                "",
                "-C",
                f"auto-penguin-setup@{hostname}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(
                "Failed to generate Ed25519 SSH keys: %s", result.stderr
            )
            return False

        # Set proper permissions
        self.key_path.chmod(0o600)
        self.pub_key_path.chmod(0o644)

        logger.info(
            "Ed25519 SSH keys generated successfully at %s", self.key_path
        )
        return True

    def configure_sshd_security(
        self,
        port: int = 22,
        password_auth: bool = False,
        permit_root_login: bool = False,
    ) -> bool:
        """Configure SSH daemon security settings.

        Creates /etc/ssh/sshd_config.d/50-autopenguin.conf with security settings.

        Args:
            port: SSH port number (default: 22)
            password_auth: Allow password authentication (default: False)
            permit_root_login: Allow root login (default: False)

        Returns:
            True on success

        """
        logger.info("Configuring SSH security settings...")

        sshd_config_dir = Path("/etc/ssh/sshd_config.d")
        config_file = sshd_config_dir / "50-autopenguin.conf"

        # Create directory if it doesn't exist
        if not sshd_config_dir.exists():
            logger.debug(
                "Creating SSH drop-in config directory: %s", sshd_config_dir
            )
            result = run_privileged(
                ["mkdir", "-p", str(sshd_config_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("Failed to create %s", sshd_config_dir)
                return False

        # Create drop-in configuration
        config_content = f"""# auto-penguin-setup SSH configuration
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Port configuration
Port {port}

# Authentication
PasswordAuthentication {"yes" if password_auth else "no"}
PubkeyAuthentication yes
PermitRootLogin {"yes" if permit_root_login else "no"}
PermitEmptyPasswords no

# Security hardening
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
"""

        result = run_privileged(
            ["tee", str(config_file)],
            stdin_input=config_content,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to write SSH configuration file")
            return False

        logger.info("SSH security configuration written to %s", config_file)
        return True

    def enable_ssh_service(self) -> bool:
        """Enable and start SSH service.

        Returns:
            True on success

        """
        try:
            service_name = self._get_ssh_service_name()
            logger.info(
                "Ensuring SSH service (%s) is running...", service_name
            )

            result = run_privileged(
                ["systemctl", "enable", "--now", service_name],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error(
                    "Failed to enable and start SSH service: %s", result.stderr
                )
                return False

            logger.info("SSH service (%s) is running", service_name)
            return True

        except RuntimeError as e:
            logger.error("Failed to enable SSH service: %s", e)
            return False

    def reload_sshd_config(self) -> bool:
        """Reload SSH daemon to apply configuration changes.

        Returns:
            True on success

        """
        try:
            service_name = self._get_ssh_service_name()
            logger.info("Reloading SSH service to apply configuration...")

            # Try reload first
            result = run_privileged(
                ["systemctl", "reload", service_name],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.warning("Reload failed, attempting restart...")
                result = run_privileged(
                    ["systemctl", "restart", service_name],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode != 0:
                    logger.error(
                        "Failed to reload/restart SSH service: %s",
                        result.stderr,
                    )
                    return False

            logger.info("SSH configuration reloaded successfully")
            return True

        except RuntimeError as e:
            logger.error("Failed to reload SSH service: %s", e)
            return False

    def copy_key_to_remote(
        self, user: str, ip: str, port: int, device_name: str | None = None
    ) -> bool:
        """Copy Ed25519 public key to remote host using ssh-copy-id.

        Args:
            user: Remote username
            ip: Remote IP address
            port: Remote SSH port
            device_name: Optional device name for logging

        Returns:
            True on success

        """
        device_label = device_name or f"{user}@{ip}:{port}"

        # Check if host is reachable
        if not self._check_host_reachable(ip, port):
            logger.warning(
                "Host %s (%s:%d) is not reachable, skipping",
                device_label,
                ip,
                port,
            )
            return False

        logger.info(
            "Copying SSH key to %s (%s@%s:%d)...", device_label, user, ip, port
        )
        logger.info("You may be prompted for password on the remote host")

        result = subprocess.run(
            [
                "ssh-copy-id",
                "-i",
                str(self.pub_key_path),
                "-p",
                str(port),
                f"{user}@{ip}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error("Failed to copy SSH key to %s", device_label)
            return False

        logger.info("SSH key copied successfully to %s", device_label)
        return True

    def test_ssh_connection(self, user: str, ip: str, port: int) -> bool:
        """Test passwordless SSH connection to remote host.

        Args:
            user: Remote username
            ip: Remote IP address
            port: Remote SSH port

        Returns:
            True if passwordless connection works

        """
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-p",
                str(port),
                f"{user}@{ip}",
                "exit",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        return result.returncode == 0

    def generate_ssh_config(self, devices: dict[str, str]) -> bool:
        """Generate ~/.ssh/config from device definitions.

        Args:
            devices: Dictionary mapping device names to "user@ip:port" strings

        Returns:
            True on success

        """
        logger.info("Generating SSH client configuration...")

        # Create .ssh directory
        self.ssh_dir.mkdir(mode=0o700, exist_ok=True)

        # Backup existing config
        if self.config_file.exists():
            backup_suffix = datetime.now().strftime(".bak.%Y%m%d%H%M%S")
            backup_path = Path(str(self.config_file) + backup_suffix)
            logger.debug("Backing up existing SSH config to %s", backup_path)
            self.config_file.rename(backup_path)

        # Generate config content
        hostname = subprocess.run(
            ["hostname"], capture_output=True, text=True, check=True
        ).stdout.strip()

        config_lines = [
            "# SSH Client Configuration",
            f"# Generated by auto-penguin-setup on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Device: {hostname}",
            "",
            "# Default settings for all hosts",
            "Host *",
            "  ServerAliveInterval 60",
            "  ServerAliveCountMax 3",
            "  ControlMaster auto",
            "  ControlPath ~/.ssh/control-%r@%h:%p",
            "  ControlPersist 10m",
            "",
            "# Auto-generated host entries",
        ]

        # Add device entries
        for device_name, device_config in devices.items():
            try:
                user, ip, port = self._parse_remote_host(device_config)
                config_lines.extend(
                    [
                        "",
                        f"Host {device_name}",
                        f"  HostName {ip}",
                        f"  User {user}",
                        f"  Port {port}",
                        "  IdentityFile ~/.ssh/id_ed25519",
                    ]
                )
                logger.debug("Added SSH config entry for %s", device_name)
            except ValueError as e:
                logger.warning(
                    "Skipping invalid device config: %s=%s (%s)",
                    device_name,
                    device_config,
                    e,
                )

        # Write config file
        self.config_file.write_text("\n".join(config_lines) + "\n")
        self.config_file.chmod(0o600)

        logger.info(
            "SSH config generated successfully at %s", self.config_file
        )
        return True

    def configure(self, **kwargs) -> bool:
        """Apply SSH configuration.

        Supported kwargs:
            port (int): SSH port (default: 22)
            password_auth (bool): Allow password authentication (default: False)
            permit_root_login (bool): Allow root login (default: False)
            enable_service (bool): Enable SSH service (default: True)
            devices (dict): Device name -> "user@ip:port" mappings
            targets (list): List of device names to copy keys to

        Returns:
            True on success

        """
        port = kwargs.get("port", 22)
        password_auth = kwargs.get("password_auth", False)
        permit_root_login = kwargs.get("permit_root_login", False)
        enable_service = kwargs.get("enable_service", True)
        devices = kwargs.get("devices", {})
        targets = kwargs.get("targets", [])

        logger.info("=" * 50)
        logger.info("Starting SSH Automated Setup")
        logger.info("=" * 50)

        # Create SSH keys
        if not self.create_ssh_keys():
            logger.error("Failed to create SSH keys")
            return False

        # Configure sshd security
        if not self.configure_sshd_security(
            port, password_auth, permit_root_login
        ):
            logger.error("Failed to configure SSH security")
            return False

        # Enable SSH service
        if enable_service:
            if not self.enable_ssh_service():
                logger.warning("Failed to enable SSH service")

            if not self.reload_sshd_config():
                logger.warning("Failed to reload SSH configuration")

        # Copy keys to targets
        if devices and targets:
            success_count = 0
            fail_count = 0

            for target in targets:
                if target not in devices:
                    logger.warning(
                        "Target device '%s' not found in device list", target
                    )
                    fail_count += 1
                    continue

                try:
                    user, ip, target_port = self._parse_remote_host(
                        devices[target]
                    )
                    if self.copy_key_to_remote(user, ip, target_port, target):
                        success_count += 1
                    else:
                        fail_count += 1
                except ValueError as e:
                    logger.error("Failed to parse target %s: %s", target, e)
                    fail_count += 1

            logger.info(
                "SSH key distribution complete: %d successful, %d failed",
                success_count,
                fail_count,
            )

        # Generate SSH config
        if devices:
            if not self.generate_ssh_config(devices):
                logger.error("Failed to generate SSH client configuration")
                return False

        # Test connections
        if devices and targets:
            logger.info("Testing SSH connections to all targets...")
            for target in targets:
                if target not in devices:
                    continue

                try:
                    user, ip, target_port = self._parse_remote_host(
                        devices[target]
                    )
                    if self.test_ssh_connection(user, ip, target_port):
                        logger.info("✓ %s - Connection OK", target)
                    else:
                        logger.warning(
                            "✗ %s - Connection failed (password may be required)",
                            target,
                        )
                except ValueError:
                    logger.warning("✗ %s - Invalid configuration", target)

        logger.info("=" * 50)
        logger.info("SSH Setup Complete")
        logger.info("=" * 50)
        return True
