"""Tests for domain models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from weatherstationdatabridge.models import (
    Configuration,
    SyncResult,
    WeatherObservation,
    WeatherUndergroundStation,
    WindyObservation,
    WindyStationInfo,
)


def test_configuration_model():
    """Test Configuration model."""
    config = Configuration(
        windy_api_key="test_windy",
        wu_api_key="test_wu",
        wu_station_ids=["KTEST1", "KTEST2"],
        windy_station_ids=["1", "2"],
        sync_interval_minutes=10,
        log_level="DEBUG",
        retry_attempts=5,
        retry_delay_seconds=10,
    )

    assert config.windy_api_key == "test_windy"
    assert config.wu_api_key == "test_wu"
    assert len(config.wu_station_ids) == 2
    assert len(config.windy_station_ids) == 2


def test_weather_observation_model():
    """Test WeatherObservation model."""
    obs = WeatherObservation(
        station_id="KTEST123",
        timestamp=datetime(2025, 10, 5, 12, 0, 0),
        temperature_c=20.0,
        humidity_percent=65.0,
    )

    assert obs.station_id == "KTEST123"
    assert obs.temperature_c == 20.0
    assert obs.wind_speed_mps is None


def test_windy_observation_model():
    """Test WindyObservation model."""
    windy_obs = WindyObservation(
        station_index=1,
        timestamp="2025-10-05 12:00:00",
        temp=20.0,
        wind=5.0,
        rh=65.0,
    )

    assert windy_obs.station_index == 1
    assert windy_obs.temp == 20.0
    assert windy_obs.winddir is None


def test_sync_result_model():
    """Test SyncResult model."""
    result = SyncResult(
        station_id="KTEST123",
        success=True,
        timestamp=datetime(2025, 10, 5, 12, 0, 0),
        observations_sent=1,
    )

    assert result.success is True
    assert result.error_message is None

    failed_result = SyncResult(
        station_id="KTEST456",
        success=False,
        timestamp=datetime(2025, 10, 5, 12, 0, 0),
        error_message="Test error",
        observations_sent=0,
    )

    assert failed_result.success is False
    assert failed_result.error_message == "Test error"
