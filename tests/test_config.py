"""Tests for configuration module."""

import os
from pathlib import Path

import pytest

from weatherstationdatabridge.config import load_configuration
from weatherstationdatabridge.models import InvalidConfiguration, MissingConfiguration


def test_load_configuration_missing_windy_key(tmp_path, monkeypatch):
    """Test missing WINDY_API_KEY."""
    # Clear all relevant env vars
    for key in ["WINDY_API_KEY", "WU_API_KEY", "WU_STATION_IDS"]:
        monkeypatch.delenv(key, raising=False)

    # Use non-existent env file to prevent loading project .env
    with pytest.raises(MissingConfiguration, match="WINDY_API_KEY"):
        load_configuration(str(tmp_path / "nonexistent.env"))


def test_load_configuration_missing_wu_key(tmp_path, monkeypatch):
    """Test missing WU_API_KEY."""
    monkeypatch.setenv("WINDY_API_KEY", "test_key")
    monkeypatch.delenv("WU_API_KEY", raising=False)
    monkeypatch.delenv("WU_STATION_IDS", raising=False)

    # Use non-existent env file to prevent loading project .env
    with pytest.raises(MissingConfiguration, match="WU_API_KEY"):
        load_configuration(str(tmp_path / "nonexistent.env"))


def test_load_configuration_missing_station_ids(tmp_path, monkeypatch):
    """Test missing WU_STATION_IDS."""
    monkeypatch.setenv("WINDY_API_KEY", "test_key")
    monkeypatch.setenv("WU_API_KEY", "test_key")
    monkeypatch.delenv("WU_STATION_IDS", raising=False)

    # Use non-existent env file to prevent loading project .env
    with pytest.raises(MissingConfiguration, match="WU_STATION_IDS"):
        load_configuration(str(tmp_path / "nonexistent.env"))


def test_load_configuration_empty_station_ids(tmp_path, monkeypatch):
    """Test empty WU_STATION_IDS."""
    # Create a test env file with empty station IDs
    test_env = tmp_path / "test.env"
    test_env.write_text(
        "WINDY_API_KEY=test_key\n"
        "WU_API_KEY=test_key\n"
        "WU_STATION_IDS=\n"
        "WINDY_STATION_IDS=1\n"
    )

    with pytest.raises(InvalidConfiguration, match="at least one station"):
        load_configuration(str(test_env))


def test_load_configuration_valid(tmp_path, monkeypatch):
    """Test valid configuration."""
    # Create a test env file
    test_env = tmp_path / "test.env"
    test_env.write_text(
        "WINDY_API_KEY=windy_key\n"
        "WU_API_KEY=wu_key\n"
        "WU_STATION_IDS=KTEST1,KTEST2,KTEST3\n"
        "WINDY_STATION_IDS=1,2,3\n"
    )

    config = load_configuration(str(test_env))

    assert config.windy_api_key == "windy_key"
    assert config.wu_api_key == "wu_key"
    assert config.wu_station_ids == ["KTEST1", "KTEST2", "KTEST3"]
    assert config.windy_station_ids == ["1", "2", "3"]
    assert config.sync_interval_minutes == 5
    assert config.log_level == "INFO"
    assert config.retry_attempts == 3
    assert config.retry_delay_seconds == 5


def test_load_configuration_with_optionals(tmp_path, monkeypatch):
    """Test configuration with optional values."""
    # Create a test env file with optional values
    test_env = tmp_path / "test.env"
    test_env.write_text(
        "WINDY_API_KEY=windy_key\n"
        "WU_API_KEY=wu_key\n"
        "WU_STATION_IDS=KTEST1\n"
        "WINDY_STATION_IDS=1\n"
        "SYNC_INTERVAL_MINUTES=10\n"
        "LOG_LEVEL=DEBUG\n"
        "RETRY_ATTEMPTS=5\n"
        "RETRY_DELAY_SECONDS=10\n"
    )

    config = load_configuration(str(test_env))

    assert config.sync_interval_minutes == 10
    assert config.log_level == "DEBUG"
    assert config.retry_attempts == 5
    assert config.retry_delay_seconds == 10


def test_load_configuration_invalid_log_level(tmp_path, monkeypatch):
    """Test invalid log level."""
    # Create a test env file with invalid log level
    test_env = tmp_path / "test.env"
    test_env.write_text(
        "WINDY_API_KEY=windy_key\n"
        "WU_API_KEY=wu_key\n"
        "WU_STATION_IDS=KTEST1\n"
        "WINDY_STATION_IDS=1\n"
        "LOG_LEVEL=INVALID\n"
    )

    with pytest.raises(InvalidConfiguration, match="LOG_LEVEL"):
        load_configuration(str(test_env))
