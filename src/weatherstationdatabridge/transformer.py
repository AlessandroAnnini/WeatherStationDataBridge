"""Data transformation module."""

import logging
from datetime import datetime
from typing import Optional

from .models import WeatherObservation, WindyObservation

logger = logging.getLogger(__name__)

# Precipitation history cache: {station_id: (timestamp, precip_mm, precip_in)}
_precipitation_cache: dict[str, tuple[datetime, Optional[float], Optional[float]]] = {}


def calculate_hourly_precipitation(
    station_id: str,
    current_timestamp: datetime,
    current_precip_mm: Optional[float],
    current_precip_in: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    """
    Calculate hourly precipitation by comparing with previous observation.

    Args:
        station_id: Weather station identifier
        current_timestamp: Timestamp of current observation
        current_precip_mm: Current daily cumulative precipitation in mm
        current_precip_in: Current daily cumulative precipitation in inches

    Returns:
        Tuple of (hourly_precip_mm, hourly_precip_in) or (None, None)

    Logic:
        - First reading: Store and return None (no previous data)
        - Normal case: hourly = current - previous
        - Midnight reset: current < previous → store new baseline, return None
        - Missing data: Return None if either current or previous is None
    """
    # Get previous reading from cache
    previous = _precipitation_cache.get(station_id)

    # Store current reading in cache
    _precipitation_cache[station_id] = (
        current_timestamp,
        current_precip_mm,
        current_precip_in,
    )

    # No previous data available
    if previous is None:
        logger.debug(f"First precipitation reading for station {station_id}")
        return None, None

    prev_timestamp, prev_precip_mm, prev_precip_in = previous

    # Calculate hourly delta for mm
    hourly_mm = None
    if current_precip_mm is not None and prev_precip_mm is not None:
        if current_precip_mm >= prev_precip_mm:
            # Normal case: precipitation increased
            hourly_mm = current_precip_mm - prev_precip_mm
        else:
            # Midnight reset: daily total reset to 0
            logger.info(
                f"Midnight reset detected for station {station_id}: "
                f"{prev_precip_mm}mm → {current_precip_mm}mm"
            )
            # After reset, current reading is the hourly amount
            # But we return None to be conservative (unclear time period)
            return None, None

    # Calculate hourly delta for inches
    hourly_in = None
    if current_precip_in is not None and prev_precip_in is not None:
        if current_precip_in >= prev_precip_in:
            hourly_in = current_precip_in - prev_precip_in
        else:
            # Midnight reset already logged above
            return None, None

    return hourly_mm, hourly_in


def clear_precipitation_cache() -> None:
    """Clear precipitation cache. Useful for testing or maintenance."""
    _precipitation_cache.clear()
    logger.debug("Precipitation cache cleared")


def transform_to_windy_format(
    observation: WeatherObservation,
    station_index: int,
) -> WindyObservation:
    """
    Transform Weather Underground observation to Windy format.

    Args:
        observation: Weather observation from WU
        station_index: Windy station index

    Returns:
        WindyObservation object

    Raises:
        ValueError: If observation contains no valid measurements
    """
    # Check if observation has at least one measurement
    has_data = any(
        [
            observation.temperature_c is not None,
            observation.wind_speed_kmh is not None,
            observation.humidity_percent is not None,
            observation.pressure_mbar is not None,
        ]
    )

    if not has_data:
        raise ValueError("Observation must contain at least one measurement")

    # Format timestamp as ISO 8601 UTC string
    timestamp_str = observation.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Convert wind speed from km/h to m/s (Windy expects m/s)
    # WU API returns km/h for metric mode, divide by 3.6 to get m/s
    wind_speed_mps = None
    if observation.wind_speed_kmh is not None:
        wind_speed_mps = observation.wind_speed_kmh / 3.6

    wind_gust_mps = None
    if observation.wind_gust_kmh is not None:
        wind_gust_mps = observation.wind_gust_kmh / 3.6

    # Convert UV index to integer if present (Windy expects integer)
    uv_value = None
    if observation.uv_index is not None:
        uv_value = int(observation.uv_index)

    # Calculate hourly precipitation from daily cumulative total
    # WU API returns 'precipTotal' (daily cumulative)
    # Windy API expects 'precip' (hourly)
    # We calculate the delta from the previous reading
    precip_hourly, rainin_hourly = calculate_hourly_precipitation(
        station_id=observation.station_id,
        current_timestamp=observation.timestamp,
        current_precip_mm=observation.precipitation_mm,
        current_precip_in=observation.precipitation_in,
    )

    return WindyObservation(
        station_index=station_index,
        timestamp=timestamp_str,
        temp=observation.temperature_c,
        tempf=observation.temperature_f,
        wind=wind_speed_mps,
        windspeedmph=observation.wind_speed_mph,
        winddir=observation.wind_direction_deg,
        gust=wind_gust_mps,
        windgustmph=observation.wind_gust_mph,
        rh=observation.humidity_percent,
        dewpoint=observation.dewpoint_c,
        pressure=None,  # Windy uses mbar instead of Pa
        mbar=observation.pressure_mbar,
        baromin=observation.pressure_inhg,
        precip=precip_hourly,
        rainin=rainin_hourly,
        uv=uv_value,
    )
