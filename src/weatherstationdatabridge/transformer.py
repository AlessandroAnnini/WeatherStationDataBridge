"""Data transformation module."""

from .models import WeatherObservation, WindyObservation


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
            observation.wind_speed_mps is not None,
            observation.humidity_percent is not None,
            observation.pressure_mbar is not None,
        ]
    )

    if not has_data:
        raise ValueError("Observation must contain at least one measurement")

    # Format timestamp as ISO 8601 UTC string
    timestamp_str = observation.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return WindyObservation(
        station_index=station_index,
        timestamp=timestamp_str,
        temp=observation.temperature_c,
        tempf=observation.temperature_f,
        wind=observation.wind_speed_mps,
        windspeedmph=observation.wind_speed_mph,
        winddir=observation.wind_direction_deg,
        gust=observation.wind_gust_mps,
        windgustmph=observation.wind_gust_mph,
        rh=observation.humidity_percent,
        dewpoint=observation.dewpoint_c,
        pressure=None,  # Windy uses mbar
        mbar=observation.pressure_mbar,
        baromin=observation.pressure_inhg,
        precip=observation.precipitation_mm,
        rainin=observation.precipitation_in,
        uv=observation.uv_index,
    )
