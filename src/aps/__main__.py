"""CLI entry point for Auto Penguin Setup."""

import logging
import sys
from pathlib import Path

from aps.cli import create_parser
from aps.cli.commands import (
    cmd_install,
    cmd_list,
    cmd_remove,
    cmd_setup,
    cmd_status,
    cmd_sync_repos,
)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging to write to ~/.config/auto-penguin-setup/logs/aps.log.

    Args:
        verbose: If True, show DEBUG messages. Otherwise show INFO and above.
    """
    log_dir = Path.home() / ".config" / "auto-penguin-setup" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "aps.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
        ],
    )

    # Add stream handler for stderr - show INFO by default, DEBUG if verbose
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(stream_handler)


def main() -> int:
    """Main entry point for the aps CLI."""
    # Parse args first to get verbose flag
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging with verbose flag
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)
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
