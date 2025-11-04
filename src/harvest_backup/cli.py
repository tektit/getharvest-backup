"""CLI interface for Harvest backup tool."""

import asyncio
import logging
import sys
from pathlib import Path

import click

from harvest_backup import __version__
from harvest_backup.api.client import HarvestAPIClient, VERBOSE
from harvest_backup.api.exceptions import HarvestAuthenticationError
from harvest_backup.backup.executor import BackupExecutor
from harvest_backup.backup.writer import BackupWriter

logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="harvest-backup")
@click.option(
    "--pat",
    envvar="HARVEST_PAT",
    required=True,
    help="Personal Access Token (or set HARVEST_PAT environment variable)",
)
@click.option(
    "--output",
    "-o",
    default="./backup",
    type=click.Path(path_type=Path),
    help="Output directory for backups (default: ./backup)",
)
@click.option(
    "--user-agent",
    default=f"HarvestBackupTool/{__version__}",
    help="User-Agent header value",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show per-request details (VERBOSE level)",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Show debug information (includes verbose + DEBUG level)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Show only errors (WARNING and above)",
)
def main(pat: str, output: Path, user_agent: str, verbose: bool, debug: bool, quiet: bool) -> None:
    """Backup tool for Harvest Time Tracking data.

    Backs up all data from all Harvest accounts using the Harvest API v2.

    Version: {version}
    """.format(
        version=__version__
    )
    # Set logging level based on flags
    # Default: Only show overview (INFO level)
    # -v: Show per-request details (VERBOSE level)
    # -d/--debug: Include -v and add DEBUG level
    # -q: Only errors (WARNING and above)

    # Suppress low-level httpx/httpcore debug logs (they're too verbose)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    if quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif debug:
        # Debug includes verbose (VERBOSE + DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        # Verbose shows per-request details (VERBOSE level)
        logging.getLogger().setLevel(VERBOSE)
    else:
        # Default: INFO level (overview INFO will show, but VERBOSE won't)
        logging.getLogger().setLevel(logging.INFO)

    async def run_backup() -> None:
        """Run the backup process."""
        client = HarvestAPIClient(pat, user_agent=user_agent)
        try:
            writer = BackupWriter(output)
            executor = BackupExecutor(client, writer)

            # Run backup
            await executor.backup_all()

            logger.info("✓ Backup completed successfully")
        except KeyboardInterrupt:
            logger.warning("Backup interrupted by user")
            sys.exit(1)
        except HarvestAuthenticationError as e:
            logger.error(f"✗ Authentication failed: {e}")
            if e.response_body:
                logger.error(f"Response details: {e.response_body}")
            logger.error("Please check your Personal Access Token (PAT) and try again.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"✗ Backup failed: {e}")
            logger.exception("Backup failed")
            sys.exit(1)
        finally:
            await client.close()

    asyncio.run(run_backup())


if __name__ == "__main__":
    main()
