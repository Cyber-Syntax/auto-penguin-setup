"""CLI command implementations for Auto Penguin Setup.

This package contains individual command modules, each handling a specific CLI command.
Commands are organized in separate modules for better maintainability and testability.
"""

from aps.cli.commands.install import cmd_install
from aps.cli.commands.list import cmd_list
from aps.cli.commands.remove import cmd_remove
from aps.cli.commands.setup import cmd_setup
from aps.cli.commands.status import cmd_status
from aps.cli.commands.sync_repos import (
    _extract_package_name,
    _parse_package_source,
    cmd_sync_repos,
)
from aps.cli.commands.upgrade import cmd_upgrade

__all__ = [
    "_extract_package_name",
    "_parse_package_source",
    "cmd_install",
    "cmd_list",
    "cmd_remove",
    "cmd_setup",
    "cmd_status",
    "cmd_sync_repos",
    "cmd_upgrade",
]
