"""UFW firewall configuration module."""

import subprocess

from aps.core.logger import get_logger
from aps.utils.privilege import run_privileged

from .base import BaseSystemConfig

logger = get_logger(__name__)


class UFWConfig(BaseSystemConfig):
    """Configure UFW (Uncomplicated Firewall) across distributions."""

    def configure(self) -> bool:
        """Set up UFW firewall with security rules.

        Disables firewalld if present and configures UFW with:
        - Default deny incoming, allow outgoing
        - Rate limiting on SSH
        - Internal network SSH access
        - Syncthing ports

        Returns:
            bool: True if configuration was successful, False otherwise.

        """
        logger.info("Setting up UFW firewall...")

        if not self._disable_firewalld():
            logger.warning("Could not disable firewalld, continuing...")

        if not self._disable_ufw():
            return False

        if not self._configure_ssh_rules():
            return False

        if not self._configure_default_policies():
            return False

        if not self._configure_syncthing_rules():
            return False

        if not self._enable_ufw():
            return False

        logger.info("UFW setup completed successfully")
        logger.info("Check status with: sudo ufw status verbose")
        return True

    def _disable_firewalld(self) -> bool:
        """Disable firewalld if it exists.

        Returns:
            bool: True always (failure is acceptable as firewalld may not exist).

        """
        try:
            result = subprocess.run(
                ["systemctl", "list-unit-files", "firewalld.service"],
                capture_output=True,
                check=False,
            )

            if result.returncode == 0:
                logger.info("Found firewalld, disabling it...")
                run_privileged(
                    ["systemctl", "disable", "--now", "firewalld"],
                    check=False,
                )

            return True

        except Exception as e:
            logger.debug("Error checking for firewalld: %s", e)
            return True

    def _disable_ufw(self) -> bool:
        """Disable UFW to avoid conflicts during configuration.

        Returns:
            bool: True if successful, False otherwise.

        """
        logger.info("Disabling UFW if it's already enabled...")

        try:
            result = run_privileged(
                ["ufw", "disable"],
                check=False,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error("Error disabling UFW: %s", e)
            return False

    def _configure_ssh_rules(self) -> bool:
        """Configure SSH rules with rate limiting and internal network access.

        Returns:
            bool: True if successful, False otherwise.

        """
        logger.info("Configuring SSH rules...")

        commands = [
            ["ufw", "limit", "22/tcp"],
            [
                "ufw",
                "allow",
                "from",
                "192.168.0.0/16",
                "to",
                "any",
                "port",
                "22",
                "proto",
                "tcp",
            ],
            ["ufw", "deny", "ssh"],
        ]

        for cmd in commands:
            try:
                result = run_privileged(cmd, check=False)

                if result.returncode != 0:
                    logger.error("Failed to execute: %s", " ".join(cmd))
                    logger.error("Output: %s", result.stderr)
                    return False

            except Exception as e:
                logger.error("Error configuring SSH rules: %s", e)
                return False

        return True

    def _configure_default_policies(self) -> bool:
        """Configure default UFW policies.

        Returns:
            bool: True if successful, False otherwise.

        """
        logger.info("Configuring UFW policies...")

        commands = [
            ["ufw", "default", "deny", "incoming"],
            ["ufw", "default", "allow", "outgoing"],
        ]

        for cmd in commands:
            try:
                result = run_privileged(cmd, check=False)

                if result.returncode != 0:
                    logger.error("Failed to execute: %s", " ".join(cmd))
                    return False

            except Exception as e:
                logger.error("Error configuring default policies: %s", e)
                return False

        return True

    def _configure_syncthing_rules(self) -> bool:
        """Configure Syncthing port rules.

        Returns:
            bool: True if successful, False otherwise.

        """
        logger.info("Configuring Syncthing rules...")

        commands = [
            ["ufw", "allow", "22000/tcp", "comment", "Syncthing"],
            ["ufw", "allow", "21027/udp", "comment", "Syncthing"],
        ]

        for cmd in commands:
            try:
                result = run_privileged(cmd, check=False)

                if result.returncode != 0:
                    logger.error("Failed to execute: %s", " ".join(cmd))
                    return False

            except Exception as e:
                logger.error("Error configuring Syncthing rules: %s", e)
                return False

        return True

    def _enable_ufw(self) -> bool:
        """Enable UFW firewall.

        Returns:
            bool: True if successful, False otherwise.

        """
        logger.info("Enabling UFW...")

        try:
            result = run_privileged(
                ["ufw", "enable"],
                check=False,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error("Error enabling UFW: %s", e)
            return False
