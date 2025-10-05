"""Weather Station Data Bridge - Main module."""

import asyncio
import logging
import sys
from pathlib import Path

import typer

from .config import load_configuration
from .health import run_health_server
from .orchestrator import create_sync_executor
from .scheduler import run_scheduler

app = typer.Typer(
    name="weatherstationdatabridge",
    help="Bridge weather data from WeatherUnderground to Windy",
)


def setup_logging(log_level: str) -> None:
    """
    Setup logging configuration.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@app.command()
def run(
    env_file: Path = typer.Option(
        None,
        "--env-file",
        "-e",
        help="Path to .env file",
    ),
) -> None:
    """Run the weather station data bridge service."""
    try:
        # Load configuration
        config = load_configuration(str(env_file) if env_file else None)

        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        logger.info("Starting Weather Station Data Bridge")
        logger.info(f"Monitoring {len(config.wu_station_ids)} stations")
        logger.info(f"Sync interval: {config.sync_interval_minutes} minutes")

        # Create sync executor
        sync_executor = create_sync_executor(config)

        # Run async event loop
        async def main():
            # Start health check server and scheduler concurrently
            await asyncio.gather(
                run_health_server(8080),
                run_scheduler(sync_executor, config.sync_interval_minutes),
            )

        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def test_sync(
    env_file: Path = typer.Option(
        None,
        "--env-file",
        "-e",
        help="Path to .env file",
    ),
) -> None:
    """Test a single sync cycle without scheduling."""
    try:
        # Load configuration
        config = load_configuration(str(env_file) if env_file else None)

        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)

        logger.info("Running test sync cycle")

        # Create and execute sync
        sync_executor = create_sync_executor(config)
        results = sync_executor()

        # Display results
        typer.echo("\nSync Results:")
        typer.echo("=" * 60)
        for result in results:
            status = "✓" if result.success else "✗"
            typer.echo(f"{status} {result.station_id}: ", nl=False)
            if result.success:
                typer.secho("SUCCESS", fg=typer.colors.GREEN)
            else:
                typer.secho(f"FAILED - {result.error_message}", fg=typer.colors.RED)

        typer.echo("=" * 60)
        successful = sum(1 for r in results if r.success)
        typer.echo(f"Total: {successful}/{len(results)} successful")

        if successful < len(results):
            sys.exit(1)

    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("Weather Station Data Bridge v1.0.0")


def main() -> None:
    """Main entry point."""
    app()
