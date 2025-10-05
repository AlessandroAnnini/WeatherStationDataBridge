"""Windy API client module."""

import logging

import httpx

from .models import (
    APIConnectionError,
    AuthenticationError,
    InvalidData,
    WindyObservation,
    WindyStationInfo,
)

logger = logging.getLogger(__name__)


def send_to_windy(
    windy_api_key: str,
    observation: WindyObservation,
    windy_station_id: str,
    timeout: float = 30.0,
) -> bool:
    """
    Send weather observation to Windy API.

    Args:
        windy_api_key: Windy API key
        observation: WindyObservation to send
        windy_station_id: Windy station ID (not the WU station ID)
        timeout: Request timeout in seconds

    Returns:
        True if successful

    Raises:
        APIConnectionError: Connection error
        AuthenticationError: Authentication error
        InvalidData: Invalid data error
    """
    # API key goes in the URL path per Windy API documentation
    url = f"https://stations.windy.com/pws/update/{windy_api_key}"

    # Build parameters - use the actual Windy station ID
    params = {
        "station": windy_station_id,
        "dateutc": observation.timestamp,
    }

    # Add optional fields if present
    fields_map = {
        "temp": observation.temp,
        "tempf": observation.tempf,
        "wind": observation.wind,
        "windspeedmph": observation.windspeedmph,
        "winddir": observation.winddir,
        "gust": observation.gust,
        "windgustmph": observation.windgustmph,
        "rh": observation.rh,
        "dewpoint": observation.dewpoint,
        "mbar": observation.mbar,
        "baromin": observation.baromin,
        "precip": observation.precip,
        "rainin": observation.rainin,
        "uv": observation.uv,
    }

    for key, value in fields_map.items():
        if value is not None:
            params[key] = value

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params)

            if response.status_code == 401:
                raise AuthenticationError("Invalid Windy API key")
            elif response.status_code == 400:
                raise InvalidData(f"Invalid data sent to Windy: {response.text}")
            elif response.status_code != 200:
                raise APIConnectionError(
                    f"Windy API returned status {response.status_code}: {response.text}"
                )

            logger.debug(
                f"Successfully sent observation to Windy for station {windy_station_id}"
            )
            return True

    except httpx.TimeoutException as e:
        raise APIConnectionError(f"Timeout connecting to Windy API: {e}") from e
    except httpx.RequestError as e:
        raise APIConnectionError(f"Error connecting to Windy API: {e}") from e


def register_windy_station(
    windy_api_key: str,
    station_info: WindyStationInfo,
    timeout: float = 30.0,
) -> bool:
    """
    Register a station with Windy API.

    Args:
        windy_api_key: Windy API key
        station_info: WindyStationInfo to register
        timeout: Request timeout in seconds

    Returns:
        True if successful

    Raises:
        APIConnectionError: Connection error
        AuthenticationError: Authentication error
    """
    url = "https://stations.windy.com/pws/register"

    # Build payload
    payload = {
        "station": station_info.station_index,
        "name": station_info.name,
        "lat": station_info.latitude,
        "lon": station_info.longitude,
    }

    if station_info.elevation is not None:
        payload["elevation"] = station_info.elevation
    if station_info.temp_height is not None:
        payload["tempheight"] = station_info.temp_height
    if station_info.wind_height is not None:
        payload["windheight"] = station_info.wind_height

    headers = {"Authorization": f"Bearer {windy_api_key}"}

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=headers)

            if response.status_code == 401:
                raise AuthenticationError("Invalid Windy API key")
            elif response.status_code == 409:
                logger.warning(f"Station {station_info.station_index} already exists")
                return True  # Consider already registered as success
            elif response.status_code != 200 and response.status_code != 201:
                raise APIConnectionError(
                    f"Windy API returned status {response.status_code}: {response.text}"
                )

            logger.info(
                f"Successfully registered station {station_info.station_index} with Windy"
            )
            return True

    except httpx.TimeoutException as e:
        raise APIConnectionError(f"Timeout connecting to Windy API: {e}") from e
    except httpx.RequestError as e:
        raise APIConnectionError(f"Error connecting to Windy API: {e}") from e
