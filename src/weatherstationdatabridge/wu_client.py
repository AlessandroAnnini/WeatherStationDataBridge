"""Weather Underground API client module."""

import logging
from datetime import datetime
from typing import Optional

import httpx

from .models import (
    APIConnectionError,
    AuthenticationError,
    RateLimitExceeded,
    StationNotFound,
    WeatherObservation,
    WeatherUndergroundStation,
)

logger = logging.getLogger(__name__)

# Station metadata cache
_station_cache: dict[str, WeatherUndergroundStation] = {}


def fetch_weather_underground_data(
    wu_api_key: str,
    station_id: str,
    timeout: float = 30.0,
) -> WeatherObservation:
    """
    Fetch current weather data from Weather Underground API.

    Args:
        wu_api_key: Weather Underground API key
        station_id: Station ID to fetch data for
        timeout: Request timeout in seconds

    Returns:
        WeatherObservation object

    Raises:
        APIConnectionError: Connection error
        AuthenticationError: Authentication error
        StationNotFound: Station not found
        RateLimitExceeded: Rate limit exceeded
    """
    url = f"https://api.weather.com/v2/pws/observations/current"
    params = {
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "apiKey": wu_api_key,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params)

            if response.status_code == 401:
                raise AuthenticationError("Invalid Weather Underground API key")
            elif response.status_code == 404:
                raise StationNotFound(f"Station {station_id} not found")
            elif response.status_code == 429:
                raise RateLimitExceeded(
                    "Rate limit exceeded for Weather Underground API"
                )
            elif response.status_code != 200:
                raise APIConnectionError(
                    f"Weather Underground API returned status {response.status_code}: {response.text}"
                )

            data = response.json()

            if "observations" not in data or not data["observations"]:
                raise StationNotFound(f"No observations found for station {station_id}")

            obs = data["observations"][0]

            # Parse observation data
            return WeatherObservation(
                station_id=station_id,
                timestamp=datetime.fromisoformat(
                    obs["obsTimeUtc"].replace("Z", "+00:00")
                ),
                temperature_c=obs.get("metric", {}).get("temp"),
                temperature_f=obs.get("imperial", {}).get("temp"),
                wind_speed_mps=obs.get("metric", {}).get("windSpeed"),
                wind_speed_mph=obs.get("imperial", {}).get("windSpeed"),
                wind_direction_deg=obs.get("winddir"),
                wind_gust_mps=obs.get("metric", {}).get("windGust"),
                wind_gust_mph=obs.get("imperial", {}).get("windGust"),
                humidity_percent=obs.get("humidity"),
                dewpoint_c=obs.get("metric", {}).get("dewpt"),
                dewpoint_f=obs.get("imperial", {}).get("dewpt"),
                pressure_mbar=obs.get("metric", {}).get("pressure"),
                pressure_inhg=obs.get("imperial", {}).get("pressure"),
                precipitation_mm=obs.get("metric", {}).get("precipTotal"),
                precipitation_in=obs.get("imperial", {}).get("precipTotal"),
                uv_index=obs.get("uv"),
            )

    except httpx.TimeoutException as e:
        raise APIConnectionError(
            f"Timeout connecting to Weather Underground API: {e}"
        ) from e
    except httpx.RequestError as e:
        raise APIConnectionError(
            f"Error connecting to Weather Underground API: {e}"
        ) from e
    except (KeyError, ValueError, TypeError) as e:
        raise APIConnectionError(
            f"Invalid response from Weather Underground API: {e}"
        ) from e


def get_station_metadata(
    wu_api_key: str,
    station_id: str,
    timeout: float = 30.0,
    use_cache: bool = True,
) -> WeatherUndergroundStation:
    """
    Get station metadata from Weather Underground API.

    Args:
        wu_api_key: Weather Underground API key
        station_id: Station ID to fetch metadata for
        timeout: Request timeout in seconds
        use_cache: Whether to use cached metadata

    Returns:
        WeatherUndergroundStation object

    Raises:
        APIConnectionError: Connection error
        StationNotFound: Station not found
    """
    # Check cache first
    if use_cache and station_id in _station_cache:
        logger.debug(f"Using cached metadata for station {station_id}")
        return _station_cache[station_id]

    url = f"https://api.weather.com/v2/pws/observations/current"
    params = {
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "apiKey": wu_api_key,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params)

            if response.status_code == 404:
                raise StationNotFound(f"Station {station_id} not found")
            elif response.status_code != 200:
                raise APIConnectionError(
                    f"Weather Underground API returned status {response.status_code}"
                )

            data = response.json()

            if "observations" not in data or not data["observations"]:
                raise StationNotFound(f"Station {station_id} not found")

            obs = data["observations"][0]

            station = WeatherUndergroundStation(
                station_id=station_id,
                name=obs.get("stationID", station_id),
                latitude=obs.get("lat", 0.0),
                longitude=obs.get("lon", 0.0),
                elevation=obs.get("metric", {}).get("elev"),
            )

            # Cache the result
            _station_cache[station_id] = station

            return station

    except httpx.TimeoutException as e:
        raise APIConnectionError(
            f"Timeout connecting to Weather Underground API: {e}"
        ) from e
    except httpx.RequestError as e:
        raise APIConnectionError(
            f"Error connecting to Weather Underground API: {e}"
        ) from e
    except (KeyError, ValueError, TypeError) as e:
        raise APIConnectionError(
            f"Invalid response from Weather Underground API: {e}"
        ) from e


def clear_station_cache() -> None:
    """Clear the station metadata cache."""
    _station_cache.clear()
