"""Argument parser construction for Auto Penguin Setup CLI."""

import argparse

from aps.core.setup import SetupManager
from aps.utils.version import get_version


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for aps CLI."""
    parser = argparse.ArgumentParser(
        prog="aps", description="Auto Penguin Setup - Cross-distro package management"
    )

    # Add version flag
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
        help="Show version and exit",
    )

    # Add global verbose flag
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    subparsers = parser.add_subparsers(dest="command")

    # aps install
    install_parser = subparsers.add_parser(
        "install",
        help="Install packages",
        epilog="""
Available categories:
  @core, @apps, @dev, @desktop, @laptop, @homeserver, @qtile, @i3, @wm-common, @games, @flatpak

Examples:
  aps install @dev
  aps install neovim lazygit
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    install_parser.add_argument("packages", nargs="+", help="Package names or @category")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    # aps remove
    remove_parser = subparsers.add_parser("remove", help="Remove packages")
    remove_parser.add_argument("packages", nargs="+")
    remove_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    # aps list
    list_parser = subparsers.add_parser("list", help="List tracked packages")
    list_parser.add_argument("--source", choices=["official", "copr", "aur", "ppa", "flatpak"])
    list_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    # aps sync-repos
    sync_parser = subparsers.add_parser("sync-repos", help="Migrate repository changes")
    sync_parser.add_argument("--auto", action="store_true", help="Auto-approve migrations")
    sync_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    # aps status
    status_parser = subparsers.add_parser("status", help="Show installation status")
    status_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    # aps setup - dynamically build component list
    available_components = SetupManager.get_available_components()
    component_list = "\n".join(
        [f"  {name:<15} - {desc}" for name, desc in sorted(available_components.items())]
    )

    setup_parser = subparsers.add_parser(
        "setup",
        help="Setup system components",
        epilog=f"""
Available components:
{component_list}

Examples:
  aps setup aur-helper
  aps setup ollama
  aps setup ohmyzsh
  aps setup brave
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    setup_parser.add_argument(
        "component", choices=list(available_components.keys()), help="Component to setup"
    )
    setup_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output (show debug messages)"
    )

    return parser
