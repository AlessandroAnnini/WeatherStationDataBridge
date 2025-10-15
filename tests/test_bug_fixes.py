"""
Tests to verify the bug fixes for wind speed, precipitation, and UV index.
"""

from datetime import datetime

from weatherstationdatabridge.models import WeatherObservation
from weatherstationdatabridge.transformer import transform_to_windy_format


def test_wind_speed_conversion_from_kmh_to_mps():
    """
    Test that wind speeds are correctly converted from km/h to m/s in transformer.

    Bug: WU API returns wind in km/h, but we were treating it as m/s.
    Fix: transformer.py now converts km/h → m/s (divide by 3.6).
    """
    # Create observation with raw wind speed from WU API (in km/h)
    observation = WeatherObservation(
        station_id="TEST123",
        timestamp=datetime(2025, 10, 15, 12, 0, 0),
        temperature_c=20.0,
        wind_speed_kmh=18.0,  # Raw value from WU API
        wind_speed_mph=11.2,  # WU's imperial value
        wind_direction_deg=270,
        wind_gust_kmh=25.0,  # Raw value from WU API
        wind_gust_mph=15.5,
        humidity_percent=65.0,
    )

    # Transform to Windy format (transformer converts km/h → m/s)
    windy_obs = transform_to_windy_format(observation, station_index=0)

    # Verify wind speeds are converted correctly
    assert (
        abs(windy_obs.wind - 5.0) < 0.01
    ), "Wind speed should be 5 m/s (18 km/h ÷ 3.6)"
    assert abs(windy_obs.gust - 6.94) < 0.01, "Gust should be 6.94 m/s (25 km/h ÷ 3.6)"

    # Verify imperial values are unchanged
    assert windy_obs.windspeedmph == 11.2
    assert windy_obs.windgustmph == 15.5


def test_precipitation_not_sent_due_to_daily_vs_hourly_mismatch():
    """
    Test that precipitation is NOT sent to Windy.

    Issue: WU returns daily cumulative total, Windy expects hourly.
    Fix: Set to None since we can't calculate hourly without historical data.
    """
    observation = WeatherObservation(
        station_id="TEST123",
        timestamp=datetime(2025, 10, 15, 12, 0, 0),
        temperature_c=20.0,
        precipitation_mm=5.0,  # This is daily total from WU
        precipitation_in=0.2,  # This is daily total from WU
        humidity_percent=65.0,
    )

    # Transform to Windy format
    windy_obs = transform_to_windy_format(observation, station_index=0)

    # Verify precipitation is NOT sent (set to None)
    assert (
        windy_obs.precip is None
    ), "Precipitation should be None (can't calculate hourly)"
    assert (
        windy_obs.rainin is None
    ), "Precipitation should be None (can't calculate hourly)"


def test_uv_index_converted_to_integer():
    """
    Test that UV index is converted to integer.

    Issue: Windy API expects integer UV index.
    Fix: Convert float to int in transformer.
    """
    # Test with float UV index
    observation = WeatherObservation(
        station_id="TEST123",
        timestamp=datetime(2025, 10, 15, 12, 0, 0),
        temperature_c=20.0,
        uv_index=5.7,  # WU might return float
        humidity_percent=65.0,
    )

    # Transform to Windy format
    windy_obs = transform_to_windy_format(observation, station_index=0)

    # Verify UV is integer
    assert isinstance(windy_obs.uv, int), "UV should be integer"
    assert windy_obs.uv == 5, "UV should be truncated to 5"


def test_uv_index_none_handling():
    """Test that None UV index is handled correctly."""
    observation = WeatherObservation(
        station_id="TEST123",
        timestamp=datetime(2025, 10, 15, 12, 0, 0),
        temperature_c=20.0,
        uv_index=None,
        humidity_percent=65.0,
    )

    # Transform to Windy format
    windy_obs = transform_to_windy_format(observation, station_index=0)

    # Verify UV is None
    assert windy_obs.uv is None, "UV should remain None if not provided"


def test_all_fixes_together():
    """
    Integration test: Verify all three fixes work together.
    """
    observation = WeatherObservation(
        station_id="TEST123",
        timestamp=datetime(2025, 10, 15, 12, 0, 0),
        temperature_c=22.0,
        temperature_f=71.6,
        wind_speed_kmh=10.0,  # Raw from WU API (will be converted to 2.78 m/s)
        wind_speed_mph=6.2,
        wind_direction_deg=270,
        wind_gust_kmh=15.0,  # Raw from WU API (will be converted to 4.17 m/s)
        wind_gust_mph=9.3,
        humidity_percent=70.0,
        dewpoint_c=16.5,
        pressure_mbar=1013.25,
        pressure_inhg=29.92,
        precipitation_mm=2.5,  # Daily total (won't be sent on first reading)
        precipitation_in=0.1,  # Daily total (won't be sent on first reading)
        uv_index=6.8,  # Will be converted to integer
    )

    # Transform to Windy format
    windy_obs = transform_to_windy_format(observation, station_index=0)

    # Verify wind speed fix (converted in transformer)
    assert abs(windy_obs.wind - 2.78) < 0.01, "Wind speed correctly converted"
    assert abs(windy_obs.gust - 4.17) < 0.01, "Gust correctly converted"

    # Verify precipitation fix
    assert windy_obs.precip is None, "Precipitation not sent (daily vs hourly issue)"
    assert windy_obs.rainin is None, "Precipitation not sent (daily vs hourly issue)"

    # Verify UV fix
    assert isinstance(windy_obs.uv, int), "UV is integer"
    assert windy_obs.uv == 6, "UV correctly truncated"

    # Verify other fields unchanged
    assert windy_obs.temp == 22.0
    assert windy_obs.rh == 70.0
    assert windy_obs.mbar == 1013.25
