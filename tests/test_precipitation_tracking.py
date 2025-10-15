"""
Tests for precipitation tracking functionality.

Tests hourly precipitation calculation from daily cumulative totals,
including midnight reset handling.
"""

from datetime import datetime, timedelta

import pytest

from weatherstationdatabridge.models import WeatherObservation
from weatherstationdatabridge.transformer import (
    calculate_hourly_precipitation,
    clear_precipitation_cache,
    transform_to_windy_format,
)


@pytest.fixture(autouse=True)
def clear_cache_before_each_test():
    """Clear precipitation cache before each test."""
    clear_precipitation_cache()
    yield
    clear_precipitation_cache()


def test_first_reading_returns_none():
    """First reading for a station should return None (no previous data)."""
    station_id = "TEST001"
    timestamp = datetime(2025, 10, 15, 12, 0, 0)

    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=timestamp,
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    assert hourly_mm is None, "First reading should return None"
    assert hourly_in is None, "First reading should return None"


def test_normal_precipitation_increase():
    """Normal case: calculate delta when precipitation increases."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # First reading: 5mm / 0.2in
    calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time,
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    # Second reading: 8mm / 0.31in (3mm / 0.11in increase)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time + timedelta(hours=1),
        current_precip_mm=8.0,
        current_precip_in=0.31,
    )

    assert hourly_mm == pytest.approx(3.0, abs=0.01), "Should calculate 3mm increase"
    assert hourly_in == pytest.approx(
        0.11, abs=0.01
    ), "Should calculate 0.11in increase"


def test_no_precipitation():
    """Test when precipitation doesn't change (no rain)."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # First reading: 5mm
    calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time,
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    # Second reading: same 5mm (no change)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time + timedelta(hours=1),
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    assert hourly_mm == 0.0, "No precipitation increase should return 0"
    assert hourly_in == 0.0, "No precipitation increase should return 0"


def test_midnight_reset():
    """Test midnight reset detection (daily total resets to 0)."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 23, 0, 0)

    # Reading before midnight: 10mm accumulated
    calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time,
        current_precip_mm=10.0,
        current_precip_in=0.4,
    )

    # Reading after midnight: reset to 2mm (midnight reset occurred)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time + timedelta(hours=2),  # Next day
        current_precip_mm=2.0,  # Reset + 2mm new rain
        current_precip_in=0.08,
    )

    # After midnight reset, we return None (conservative approach)
    assert hourly_mm is None, "Midnight reset should return None"
    assert hourly_in is None, "Midnight reset should return None"


def test_multiple_stations_tracked_separately():
    """Test that multiple stations are tracked independently."""
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # Station 1: First reading
    calculate_hourly_precipitation(
        station_id="STATION_A",
        current_timestamp=base_time,
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    # Station 2: First reading
    calculate_hourly_precipitation(
        station_id="STATION_B",
        current_timestamp=base_time,
        current_precip_mm=10.0,
        current_precip_in=0.4,
    )

    # Station 1: Second reading (+3mm)
    hourly_mm_a, _ = calculate_hourly_precipitation(
        station_id="STATION_A",
        current_timestamp=base_time + timedelta(hours=1),
        current_precip_mm=8.0,
        current_precip_in=0.31,
    )

    # Station 2: Second reading (+5mm)
    hourly_mm_b, _ = calculate_hourly_precipitation(
        station_id="STATION_B",
        current_timestamp=base_time + timedelta(hours=1),
        current_precip_mm=15.0,
        current_precip_in=0.59,
    )

    assert hourly_mm_a == pytest.approx(3.0, abs=0.01), "Station A: 3mm increase"
    assert hourly_mm_b == pytest.approx(5.0, abs=0.01), "Station B: 5mm increase"


def test_none_precipitation_values():
    """Test handling of None precipitation values."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # First reading with None
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time,
        current_precip_mm=None,
        current_precip_in=None,
    )

    assert hourly_mm is None
    assert hourly_in is None

    # Second reading with actual values (previous was None)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time + timedelta(hours=1),
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    assert hourly_mm is None, "Cannot calculate delta from None"
    assert hourly_in is None, "Cannot calculate delta from None"


def test_clear_cache():
    """Test that cache clearing works."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # First reading
    calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time,
        current_precip_mm=5.0,
        current_precip_in=0.2,
    )

    # Clear cache
    clear_precipitation_cache()

    # Next reading should behave like first reading (no previous data)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id=station_id,
        current_timestamp=base_time + timedelta(hours=1),
        current_precip_mm=8.0,
        current_precip_in=0.31,
    )

    assert hourly_mm is None, "After cache clear, should return None"
    assert hourly_in is None, "After cache clear, should return None"


def test_integration_with_transformer():
    """Integration test: verify transformer uses precipitation tracking."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # First observation
    obs1 = WeatherObservation(
        station_id=station_id,
        timestamp=base_time,
        temperature_c=20.0,
        humidity_percent=65.0,
        precipitation_mm=5.0,
        precipitation_in=0.2,
    )

    windy_obs1 = transform_to_windy_format(obs1, station_index=0)

    # First reading should have None precipitation
    assert windy_obs1.precip is None, "First reading returns None"
    assert windy_obs1.rainin is None, "First reading returns None"

    # Second observation (1 hour later, +3mm rain)
    obs2 = WeatherObservation(
        station_id=station_id,
        timestamp=base_time + timedelta(hours=1),
        temperature_c=20.0,
        humidity_percent=70.0,
        precipitation_mm=8.0,
        precipitation_in=0.31,
    )

    windy_obs2 = transform_to_windy_format(obs2, station_index=0)

    # Second reading should calculate delta
    assert windy_obs2.precip == pytest.approx(
        3.0, abs=0.01
    ), "Should calculate 3mm hourly"
    assert windy_obs2.rainin == pytest.approx(
        0.11, abs=0.01
    ), "Should calculate 0.11in hourly"


def test_sequence_of_readings():
    """Test a realistic sequence of precipitation readings."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 10, 0, 0)

    # 10:00 AM - First reading: 2mm
    hourly1, _ = calculate_hourly_precipitation(station_id, base_time, 2.0, 0.08)
    assert hourly1 is None  # First reading

    # 11:00 AM - Light rain: 2mm → 5mm (3mm increase)
    hourly2, _ = calculate_hourly_precipitation(
        station_id, base_time + timedelta(hours=1), 5.0, 0.2
    )
    assert hourly2 == pytest.approx(3.0, abs=0.01)

    # 12:00 PM - Heavy rain: 5mm → 15mm (10mm increase)
    hourly3, _ = calculate_hourly_precipitation(
        station_id, base_time + timedelta(hours=2), 15.0, 0.59
    )
    assert hourly3 == pytest.approx(10.0, abs=0.01)

    # 1:00 PM - No rain: 15mm → 15mm (0mm increase)
    hourly4, _ = calculate_hourly_precipitation(
        station_id, base_time + timedelta(hours=3), 15.0, 0.59
    )
    assert hourly4 == 0.0

    # Next day 2:00 AM - After midnight reset: 15mm → 1mm
    hourly5, _ = calculate_hourly_precipitation(
        station_id, base_time + timedelta(hours=16), 1.0, 0.04
    )
    assert hourly5 is None  # Midnight reset detected


def test_edge_case_very_small_increase():
    """Test very small precipitation increases (0.1mm)."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # First reading: 0.5mm
    calculate_hourly_precipitation(station_id, base_time, 0.5, 0.02)

    # Second reading: 0.6mm (0.1mm increase)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id, base_time + timedelta(hours=1), 0.6, 0.024
    )

    assert hourly_mm == pytest.approx(0.1, abs=0.01), "Should detect small increase"
    assert hourly_in == pytest.approx(0.004, abs=0.001), "Should detect small increase"


def test_edge_case_large_accumulation():
    """Test large precipitation accumulation (heavy storm)."""
    station_id = "TEST001"
    base_time = datetime(2025, 10, 15, 12, 0, 0)

    # Before storm: 5mm
    calculate_hourly_precipitation(station_id, base_time, 5.0, 0.2)

    # After heavy storm: 5mm → 105mm (100mm increase)
    hourly_mm, hourly_in = calculate_hourly_precipitation(
        station_id, base_time + timedelta(hours=1), 105.0, 4.13
    )

    assert hourly_mm == pytest.approx(100.0, abs=0.1), "Should handle large increases"
    assert hourly_in == pytest.approx(3.93, abs=0.01), "Should handle large increases"
