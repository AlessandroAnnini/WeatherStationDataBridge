"""Tests for data transformation module."""

from datetime import datetime

import pytest

from weatherstationdatabridge.models import WeatherObservation
from weatherstationdatabridge.transformer import transform_to_windy_format


def test_transform_to_windy_format():
    """Test basic transformation."""
    observation = WeatherObservation(
        station_id="KTEST123",
        timestamp=datetime(2025, 10, 5, 12, 0, 0),
        temperature_c=20.0,
        temperature_f=68.0,
        wind_speed_kmh=18.0,  # Will be converted to 5.0 m/s in transformer
        wind_speed_mph=11.2,
        wind_direction_deg=180,
        humidity_percent=65.0,
        pressure_mbar=1013.25,
    )

    windy_obs = transform_to_windy_format(observation, station_index=1)

    assert windy_obs.station_index == 1
    assert windy_obs.timestamp == "2025-10-05 12:00:00"
    assert windy_obs.temp == 20.0
    assert windy_obs.tempf == 68.0
    assert abs(windy_obs.wind - 5.0) < 0.01  # 18 km/h ÷ 3.6 = 5.0 m/s
    assert windy_obs.windspeedmph == 11.2
    assert windy_obs.winddir == 180
    assert windy_obs.rh == 65.0
    assert windy_obs.mbar == 1013.25


def test_transform_with_minimal_data():
    """Test transformation with minimal data."""
    observation = WeatherObservation(
        station_id="KTEST123",
        timestamp=datetime(2025, 10, 5, 12, 0, 0),
        temperature_c=20.0,
    )

    windy_obs = transform_to_windy_format(observation, station_index=2)

    assert windy_obs.station_index == 2
    assert windy_obs.temp == 20.0
    assert windy_obs.wind is None
    assert windy_obs.winddir is None


def test_transform_with_no_data():
    """Test transformation with no measurements fails."""
    observation = WeatherObservation(
        station_id="KTEST123",
        timestamp=datetime(2025, 10, 5, 12, 0, 0),
    )

    with pytest.raises(ValueError, match="at least one measurement"):
        transform_to_windy_format(observation, station_index=1)
