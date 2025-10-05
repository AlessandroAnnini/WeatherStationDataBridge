"""Task scheduler module."""

import asyncio
import logging
import signal
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)

_shutdown_flag = False


def handle_shutdown_signal(signum, frame) -> None:
    """Handle shutdown signals."""
    global _shutdown_flag
    logger.info(f"Received shutdown signal {signum}")
    _shutdown_flag = True


async def run_scheduler(
    sync_executor: Callable,
    interval_minutes: int,
) -> None:
    """
    Run the sync scheduler.

    Args:
        sync_executor: Function to execute sync cycle
        interval_minutes: Interval between syncs in minutes
    """
    logger.info(f"Starting scheduler with {interval_minutes} minute interval")

    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    interval_seconds = interval_minutes * 60

    while not _shutdown_flag:
        try:
            logger.info("Executing sync cycle")
            start_time = datetime.now()

            # Execute sync in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, sync_executor)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Sync cycle completed in {elapsed:.2f}s")

            # Update health status
            from .health import update_health_status

            any_success = any(r.success for r in results)
            update_health_status(any_success)

            # Wait for next interval (or until shutdown)
            wait_time = max(0, interval_seconds - elapsed)
            logger.info(f"Waiting {wait_time:.0f}s until next sync")

            for _ in range(int(wait_time)):
                if _shutdown_flag:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in scheduler: {e}", exc_info=True)
            # Wait a bit before retrying
            await asyncio.sleep(10)

    logger.info("Scheduler shutting down gracefully")
