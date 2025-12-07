"""CLI command modules for Auto Penguin Setup."""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for aps CLI."""
    parser = argparse.ArgumentParser(
        prog="aps", description="Auto Penguin Setup - Cross-distro package management"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    # aps remove
    remove_parser = subparsers.add_parser("remove", help="Remove packages")
    remove_parser.add_argument("packages", nargs="+")

    # aps list
    list_parser = subparsers.add_parser("list", help="List tracked packages")
    list_parser.add_argument("--source", choices=["official", "copr", "aur", "ppa", "flatpak"])

    # aps sync-repos
    sync_parser = subparsers.add_parser("sync-repos", help="Migrate repository changes")
    sync_parser.add_argument("--auto", action="store_true", help="Auto-approve migrations")

    # aps status
    subparsers.add_parser("status", help="Show installation status")

    # aps setup
    setup_parser = subparsers.add_parser(
        "setup",
        help="Setup system components",
        epilog="""
Available components:
  aur-helper - Install paru AUR helper (Arch Linux only)
  ollama     - Install/update Ollama AI runtime

Examples:
  aps setup aur-helper
  aps setup ollama
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    setup_parser.add_argument(
        "component", choices=["aur-helper", "ollama"], help="Component to setup"
    )

    return parser
