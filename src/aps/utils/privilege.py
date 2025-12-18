"""Utility functions for privilege escalation."""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def run_privileged(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    stdin_input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with privilege escalation if needed.

    Args:
        cmd: Command to run as a list of strings
        env: Optional environment variables to pass
        check: Whether to raise CalledProcessError on non-zero exit (default: True)
        capture_output: Whether to capture stdout/stderr (default: True)
        text: Whether to decode output as text (default: True)
        stdin_input: Optional input to pass via stdin

    Returns:
        CompletedProcess instance

    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Running privileged command: %s", " ".join(cmd))

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            env=env,
            input=stdin_input,
        )
    return subprocess.run(
        ["sudo", "--", *cmd],
        check=check,
        capture_output=capture_output,
        text=text,
        env=env,
        input=stdin_input,
    )


def ensure_sudo() -> None:
    """Pre-authenticate sudo to avoid repeated prompts.

    Skips authentication if:
    - Already running as root
    - Running in test environment (PYTEST_CURRENT_TEST is set)
    """
    # Skip if running as root
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return

    # Skip if running in pytest
    if "PYTEST_CURRENT_TEST" in os.environ:
        return

    subprocess.run(["sudo", "-v"], check=True)
