# Weather Station Data Bridge

A lightweight Python application that fetches weather data from Weather Underground stations and forwards it to Windy.com every 5 minutes, with accurate unit conversions and precipitation tracking.

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Architecture Guide](ARCHITECTURE.md)** - Design philosophy and patterns
- **[Project Summary](SUMMARY.md)** - Complete feature overview
- **[Precipitation Tracking](PRECIPITATION_TRACKING.md)** - How hourly precipitation calculation works

## Features

### Core Functionality

- ✅ Fetches real-time weather data from multiple Weather Underground stations
- ✅ Transforms and forwards data to Windy.com with accurate unit conversions
- ✅ Configurable sync intervals (default: 5 minutes)
- ✅ Automatic retry with exponential backoff
- ✅ Timestamp deduplication to prevent duplicate API submissions
- ✅ Concurrent processing of multiple stations
- ✅ Health check endpoint for monitoring
- ✅ Structured logging
- ✅ Graceful shutdown handling
- ✅ Low resource usage (<128MB memory, <0.5 CPU cores)

### Data Quality & Accuracy

- ✅ **Correct wind speed conversion** (km/h → m/s) - fixes Weather Underground's metric units
- ✅ **Hourly precipitation tracking** - calculates deltas from WU's daily cumulative totals
- ✅ **Midnight reset detection** - handles daily precipitation reset gracefully
- ✅ **Per-station tracking** - independent precipitation history for each station
- ✅ **UV index as integer** - proper format as required by Windy API

## Architecture

Built using functional composition (no OOP), following DRY and KISS principles:

- **config.py**: Configuration loading from environment variables
- **wu_client.py**: Weather Underground API client (fetches raw data)
- **transformer.py**: ALL data transformations (wind conversion, precipitation tracking, UV conversion)
- **windy_client.py**: Windy API client
- **orchestrator.py**: Sync orchestration with concurrency control
- **scheduler.py**: Task scheduling
- **health.py**: Health check HTTP endpoint
- **retry.py**: Retry logic with exponential backoff

### Data Transformation Details

**All transformations happen in `transformer.py`** for consistency (KISS principle: single place for all data quality logic).

#### Wind Speed Conversion

Weather Underground's metric API returns wind speeds in **km/h**, but Windy expects **m/s**.

- **Where**: `wu_client.py` fetches raw km/h → `transformer.py` converts to m/s
- **Formula**: `wind_speed_kmh / 3.6 = wind_speed_mps`
- **Example**: 18 km/h → 5 m/s ✓

#### Precipitation Tracking

Weather Underground provides **daily cumulative totals**, but Windy expects **hourly precipitation**.

- **Where**: `transformer.py`
- Maintains in-memory cache of previous readings per station
- Calculates hourly delta: `current_total - previous_total`
- Detects midnight reset (when daily total resets to 0)
- Returns None for first reading or after midnight reset (conservative approach)

#### UV Index

Converts UV index from float to integer as required by Windy API.

- **Where**: `transformer.py`
- **Example**: 5.7 → 5 (truncated to integer)

## Requirements

- Python 3.11+
- UV package manager
- Weather Underground API key
- Windy API key

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd WeatherStationDataBridge
```

2. Install dependencies using UV:

```bash
uv sync
```

3. Create `.env` file from the example:

```bash
cp .env.example .env
```

4. Edit `.env` and add your API keys and station IDs:

```env
WINDY_API_KEY=your_windy_api_key
WU_API_KEY=your_wu_api_key
WU_STATION_IDS=KSTATION1,KSTATION2,KSTATION3
WINDY_STATION_IDS=0,1,2
```

## Usage

### Run the service

```bash
uv run weatherstationdatabridge run
```

Or with a custom .env file:

```bash
uv run weatherstationdatabridge run --env-file /path/to/.env
```

### Test a single sync cycle

```bash
uv run weatherstationdatabridge test-sync
```

### Check version

```bash
uv run weatherstationdatabridge version
```

## Configuration

All configuration is done via environment variables:

| Variable                | Required | Default | Description                                             |
| ----------------------- | -------- | ------- | ------------------------------------------------------- |
| `WINDY_API_KEY`         | Yes      | -       | Windy API key                                           |
| `WU_API_KEY`            | Yes      | -       | Weather Underground API key                             |
| `WU_STATION_IDS`        | Yes      | -       | Comma-separated Weather Underground station IDs         |
| `WINDY_STATION_IDS`     | Yes      | -       | Comma-separated Windy station IDs (must match WU order) |
| `SYNC_INTERVAL_MINUTES` | No       | 5       | Sync interval in minutes                                |
| `LOG_LEVEL`             | No       | INFO    | Log level (DEBUG, INFO, WARNING, ERROR)                 |
| `RETRY_ATTEMPTS`        | No       | 3       | Number of retry attempts                                |
| `RETRY_DELAY_SECONDS`   | No       | 5       | Initial delay between retries                           |

## Health Check

The service exposes a health check endpoint on `http://localhost:8080/health`:

- Returns `200 OK` if healthy
- Returns `503 Service Unavailable` if unhealthy (no successful sync in 15 minutes)

## Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --frozen

# Expose health check port
EXPOSE 8080

# Run the service
CMD ["uv", "run", "weatherstationdatabridge", "run"]
```

Build and run:

```bash
docker build -t weather-bridge .
docker run -d \
  -e WINDY_API_KEY=your_key \
  -e WU_API_KEY=your_key \
  -e WU_STATION_IDS=KSTATION1,KSTATION2 \
  -e WINDY_STATION_IDS=0,1 \
  -p 8080:8080 \
  --name weather-bridge \
  weather-bridge
```

## Development

### Install development dependencies

```bash
uv sync --group dev
```

### Run tests

```bash
# Run all tests (30 tests)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test suites
uv run pytest tests/test_bug_fixes.py         # Bug fix verification
uv run pytest tests/test_precipitation_tracking.py  # Precipitation tracking
uv run pytest tests/test_transformer.py       # Data transformation
```

### Run linting

```bash
uv run ruff check src/
```

### Run type checking

```bash
uv run mypy src/
```

### Test Coverage

The project includes comprehensive tests covering:

- **Bug fixes** (5 tests): Wind speed conversion, precipitation, UV index
- **Precipitation tracking** (11 tests): Hourly calculation, midnight reset, edge cases
- **Data transformation** (3 tests): Format conversion, validation
- **Configuration** (7 tests): Config loading, validation
- **Models** (4 tests): Pydantic model validation

## Project Structure

```
WeatherStationDataBridge/
├── src/
│   └── weatherstationdatabridge/
│       ├── __init__.py          # Main CLI entry point
│       ├── models.py             # Domain models (Pydantic)
│       ├── config.py             # Configuration loader
│       ├── wu_client.py          # Weather Underground client
│       ├── transformer.py        # Data transformation
│       ├── windy_client.py       # Windy API client
│       ├── orchestrator.py       # Sync orchestration
│       ├── scheduler.py          # Task scheduler
│       ├── health.py             # Health check endpoint
│       └── retry.py              # Retry logic
├── layereddsl.yml               # Architecture specification
├── pyproject.toml               # Project configuration
├── uv.lock                      # Lock file
├── .env.example                 # Example environment file
└── README.md                    # This file
```

## Error Handling

The application handles various error conditions:

- **APIConnectionError**: Network/connection issues
- **AuthenticationError**: Invalid API keys
- **StationNotFound**: Invalid station IDs
- **RateLimitExceeded**: API rate limits
- **MaxRetriesExceeded**: Retry limit reached

Failed syncs are logged and reported in the sync results, but don't stop the service.

## Logging

Structured logging with timestamps and log levels:

```
2025-10-05 12:00:00 [INFO] weatherstationdatabridge: Starting Weather Station Data Bridge
2025-10-05 12:00:00 [INFO] weatherstationdatabridge: Monitoring 3 stations
2025-10-05 12:00:05 [INFO] orchestrator: Syncing station KSTATION1 (index 0)
2025-10-05 12:00:06 [INFO] orchestrator: Successfully synced station KSTATION1
```

## License

MIT

## Additional Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup instructions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical design and patterns
- **[SUMMARY.md](SUMMARY.md)** - Complete project overview
- **[PRECIPITATION_TRACKING.md](PRECIPITATION_TRACKING.md)** - Precipitation tracking implementation details
- **[layereddsl.yml](layereddsl.yml)** - Formal architecture specification

## Data Quality Notes

### Important: Wind Speed Data

If you have historical wind speed data stored from previous versions, note that wind speeds were incorrectly reported **3.6× too high** before the fix. To correct historical data, divide stored wind speeds by 3.6.

### Precipitation Tracking Behavior

- **First reading**: Returns `None` (no previous data to calculate hourly delta)
- **After midnight reset**: Returns `None` (conservative approach to avoid incorrect calculations)
- **Cache lifetime**: In-memory only - cleared on application restart

For detailed technical documentation on precipitation tracking, see [PRECIPITATION_TRACKING.md](PRECIPITATION_TRACKING.md).

## Author

Weather Data Integration Team
