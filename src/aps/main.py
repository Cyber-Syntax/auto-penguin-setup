"""CLI entry point for Auto Penguin Setup."""

import sys

from aps.cli.commands import (
    cmd_install,
    cmd_list,
    cmd_remove,
    cmd_setup,
    cmd_status,
    cmd_sync_repos,
)
from aps.cli.parser import create_parser
from aps.core.logger import get_logger, setup_logging


def main() -> int:
    """Main entry point for the aps CLI."""
    # Parse args first to get verbose flag
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging with verbose flag
    setup_logging(verbose=args.verbose)
    logger = get_logger(__name__)
    logger.debug("Starting aps CLI")

    # Dispatch to command handlers
    command_handlers = {
        "install": cmd_install,
        "remove": cmd_remove,
        "list": cmd_list,
        "sync-repos": cmd_sync_repos,
        "status": cmd_status,
        "setup": cmd_setup,
    }

    handler = command_handlers.get(args.command)
    if handler:
        logger.debug("Executing command: %s", args.command)
        handler(args)
        logger.debug("Command %s completed successfully", args.command)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
