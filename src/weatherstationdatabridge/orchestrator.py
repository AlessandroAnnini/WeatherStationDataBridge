"""Sync orchestration module."""

import asyncio
import logging
from datetime import datetime
from typing import Callable

from .models import Configuration, SyncResult
from .retry import retry_with_backoff
from .transformer import transform_to_windy_format
from .windy_client import send_to_windy
from .wu_client import fetch_weather_underground_data

logger = logging.getLogger(__name__)

# Track last sent timestamp per station to avoid duplicate submissions
_last_sent_timestamps: dict[str, datetime] = {}


async def sync_station(
    station_id: str,
    windy_station_id: str,
    config: Configuration,
) -> SyncResult:
    """
    Sync a single weather station.

    Args:
        station_id: Weather Underground station ID
        windy_station_id: Windy station ID
        config: Application configuration

    Returns:
        SyncResult object
    """
    start_time = datetime.now()

    try:
        logger.info(f"Syncing station {station_id} → Windy {windy_station_id}")

        # Fetch data from Weather Underground
        observation = fetch_weather_underground_data(config.wu_api_key, station_id)
        logger.debug(f"Fetched observation for {station_id}")

        # Skip if timestamp already sent (prevents duplicate submission warnings)
        if _last_sent_timestamps.get(station_id) == observation.timestamp:
            logger.info(
                f"Skipping station {station_id}: observation already sent "
                f"(timestamp {observation.timestamp})"
            )
            return SyncResult(
                station_id=station_id,
                success=True,
                timestamp=start_time,
                observations_sent=0,
            )

        # Mark timestamp as seen before attempting send
        # This prevents retrying the same timestamp on failure
        _last_sent_timestamps[station_id] = observation.timestamp

        # Transform to Windy format (station_index is just for internal tracking, not used by API)
        windy_obs = transform_to_windy_format(observation, 0)
        logger.debug(f"Transformed observation for {station_id}")

        # Send to Windy with retry logic
        def send_operation() -> bool:
            return send_to_windy(config.windy_api_key, windy_obs, windy_station_id)

        await retry_with_backoff(
            send_operation,
            config.retry_attempts,
            config.retry_delay_seconds,
            f"send_to_windy[{station_id}→{windy_station_id}]",
        )

        logger.info(
            f"Successfully synced station {station_id} → Windy {windy_station_id}"
        )

        return SyncResult(
            station_id=station_id,
            success=True,
            timestamp=start_time,
            observations_sent=1,
        )

    except Exception as e:
        logger.error(f"Failed to sync station {station_id}: {e}")
        return SyncResult(
            station_id=station_id,
            success=False,
            timestamp=start_time,
            error_message=str(e),
            observations_sent=0,
        )


async def execute_sync_cycle(config: Configuration) -> list[SyncResult]:
    """
    Execute a complete sync cycle for all stations.

    Args:
        config: Application configuration

    Returns:
        List of SyncResult objects
    """
    logger.info(f"Starting sync cycle for {len(config.wu_station_ids)} stations")

    # Create tasks for all stations (with max concurrency of 2 as per spec)
    semaphore = asyncio.Semaphore(2)

    async def sync_with_semaphore(station_id: str, windy_station_id: str) -> SyncResult:
        async with semaphore:
            return await sync_station(station_id, windy_station_id, config)

    tasks = [
        sync_with_semaphore(wu_id, windy_id)
        for wu_id, windy_id in zip(config.wu_station_ids, config.windy_station_ids)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Log summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    logger.info(f"Sync cycle completed: {successful} successful, {failed} failed")

    return results


def create_sync_executor(config: Configuration) -> Callable[[], list[SyncResult]]:
    """
    Create a sync executor function with the given configuration.

    Args:
        config: Application configuration

    Returns:
        Sync executor function
    """

    def execute() -> list[SyncResult]:
        return asyncio.run(execute_sync_cycle(config))

    return execute
