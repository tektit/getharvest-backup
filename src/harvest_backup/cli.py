"""CLI interface for Harvest backup tool."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from harvest_backup.api.client import HarvestAPIClient
from harvest_backup.backup.executor import BackupExecutor
from harvest_backup.backup.writer import BackupWriter

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


@click.command()
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
    default="HarvestBackupTool/0.1.0",
    help="User-Agent header value",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't actually write files, just show what would be done",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(pat: str, output: Path, user_agent: str, dry_run: bool, verbose: bool) -> None:
    """Backup tool for Harvest Time Tracking data.

    Backs up all data from all Harvest accounts using the Harvest API v2.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be written[/yellow]")

    async def run_backup() -> None:
        """Run the backup process."""
        try:
            async with HarvestAPIClient(pat, user_agent=user_agent) as client:
                writer = BackupWriter(output)
                executor = BackupExecutor(client, writer, dry_run=dry_run)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Backing up Harvest accounts...", total=None)
                    await executor.backup_all()
                    progress.update(task, completed=True)

                console.print("[green]✓ Backup completed successfully[/green]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Backup interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗ Backup failed: {e}[/red]", style="bold")
            logger.exception("Backup failed")
            sys.exit(1)

    asyncio.run(run_backup())


if __name__ == "__main__":
    main()

