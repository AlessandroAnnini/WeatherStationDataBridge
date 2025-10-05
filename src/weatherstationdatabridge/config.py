"""Configuration loading module."""

import os
from typing import Optional

from dotenv import load_dotenv

from .models import Configuration, InvalidConfiguration, MissingConfiguration


def load_configuration(env_file: Optional[str] = None) -> Configuration:
    """
    Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file

    Returns:
        Configuration object

    Raises:
        MissingConfiguration: If required environment variables are missing
        InvalidConfiguration: If configuration values are invalid
    """
    if env_file:
        load_dotenv(env_file, override=True)
    else:
        # Only load .env if it exists, don't override existing env vars
        load_dotenv(override=False)

    # Required variables
    windy_api_key = os.getenv("WINDY_API_KEY")
    wu_api_key = os.getenv("WU_API_KEY")
    wu_station_ids_str = os.getenv("WU_STATION_IDS")
    windy_station_ids_str = os.getenv("WINDY_STATION_IDS")

    if not windy_api_key:
        raise MissingConfiguration("WINDY_API_KEY environment variable is required")
    if not wu_api_key:
        raise MissingConfiguration("WU_API_KEY environment variable is required")
    if wu_station_ids_str is None:
        raise MissingConfiguration("WU_STATION_IDS environment variable is required")
    if windy_station_ids_str is None:
        raise MissingConfiguration("WINDY_STATION_IDS environment variable is required")

    # Parse station IDs (comma-separated)
    wu_station_ids = [
        sid.strip() for sid in wu_station_ids_str.split(",") if sid.strip()
    ]
    windy_station_ids = [
        sid.strip() for sid in windy_station_ids_str.split(",") if sid.strip()
    ]

    if not wu_station_ids:
        raise InvalidConfiguration(
            "WU_STATION_IDS must contain at least one station ID"
        )
    if not windy_station_ids:
        raise InvalidConfiguration(
            "WINDY_STATION_IDS must contain at least one station ID"
        )
    if len(wu_station_ids) != len(windy_station_ids):
        raise InvalidConfiguration(
            f"WU_STATION_IDS ({len(wu_station_ids)}) and WINDY_STATION_IDS ({len(windy_station_ids)}) "
            "must have the same number of stations"
        )

    # Optional variables with defaults
    sync_interval_minutes = int(os.getenv("SYNC_INTERVAL_MINUTES", "5"))
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    retry_attempts = int(os.getenv("RETRY_ATTEMPTS", "3"))
    retry_delay_seconds = int(os.getenv("RETRY_DELAY_SECONDS", "5"))

    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    if log_level not in valid_log_levels:
        raise InvalidConfiguration(
            f"LOG_LEVEL must be one of {valid_log_levels}, got {log_level}"
        )

    try:
        return Configuration(
            windy_api_key=windy_api_key,
            wu_api_key=wu_api_key,
            wu_station_ids=wu_station_ids,
            windy_station_ids=windy_station_ids,
            sync_interval_minutes=sync_interval_minutes,
            log_level=log_level,
            retry_attempts=retry_attempts,
            retry_delay_seconds=retry_delay_seconds,
        )
    except Exception as e:
        raise InvalidConfiguration(f"Invalid configuration: {e}") from e
