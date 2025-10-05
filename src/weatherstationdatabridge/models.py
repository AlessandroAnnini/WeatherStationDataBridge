"""Domain models for the weather station data bridge."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """Application configuration."""

    windy_api_key: str
    wu_api_key: str
    wu_station_ids: list[str]
    windy_station_ids: list[str]
    sync_interval_minutes: int = 5
    log_level: str = "INFO"
    retry_attempts: int = 3
    retry_delay_seconds: int = 5


class WeatherUndergroundStation(BaseModel):
    """Weather Underground station metadata."""

    station_id: str
    name: str
    latitude: float
    longitude: float
    elevation: Optional[float] = None


class WeatherObservation(BaseModel):
    """Weather observation from Weather Underground."""

    station_id: str
    timestamp: datetime
    temperature_c: Optional[float] = None
    temperature_f: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    wind_direction_deg: Optional[int] = None
    wind_gust_mps: Optional[float] = None
    wind_gust_mph: Optional[float] = None
    humidity_percent: Optional[float] = None
    dewpoint_c: Optional[float] = None
    dewpoint_f: Optional[float] = None
    pressure_pa: Optional[float] = None
    pressure_mbar: Optional[float] = None
    pressure_inhg: Optional[float] = None
    precipitation_mm: Optional[float] = None
    precipitation_in: Optional[float] = None
    uv_index: Optional[float] = None


class WindyStationInfo(BaseModel):
    """Windy station information."""

    station_index: int
    name: str
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    temp_height: Optional[float] = None
    wind_height: Optional[float] = None


class WindyObservation(BaseModel):
    """Weather observation formatted for Windy API."""

    model_config = {"populate_by_name": True}

    station_index: int = Field(alias="station")
    timestamp: str = Field(alias="dateutc")
    temp: Optional[float] = None
    tempf: Optional[float] = None
    wind: Optional[float] = None
    windspeedmph: Optional[float] = None
    winddir: Optional[int] = None
    gust: Optional[float] = None
    windgustmph: Optional[float] = None
    rh: Optional[float] = None
    dewpoint: Optional[float] = None
    pressure: Optional[float] = None
    mbar: Optional[float] = None
    baromin: Optional[float] = None
    precip: Optional[float] = None
    rainin: Optional[float] = None
    uv: Optional[float] = None


class SyncResult(BaseModel):
    """Result of a sync operation."""

    station_id: str
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None
    observations_sent: int


class APIError(Exception):
    """Base exception for API errors."""

    pass


class APIConnectionError(APIError):
    """API connection error."""

    pass


class AuthenticationError(APIError):
    """API authentication error."""

    pass


class StationNotFound(APIError):
    """Station not found error."""

    pass


class RateLimitExceeded(APIError):
    """Rate limit exceeded error."""

    pass


class MissingConfiguration(Exception):
    """Missing configuration error."""

    pass


class InvalidConfiguration(Exception):
    """Invalid configuration error."""

    pass


class InvalidData(Exception):
    """Invalid data error."""

    pass


class MaxRetriesExceeded(Exception):
    """Max retries exceeded error."""

    pass
