# Weather Station Data Bridge

A lightweight Python application that fetches weather data from WeatherUnderground stations and forwards it to Windy.com every 5 minutes.

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Architecture Guide](ARCHITECTURE.md)** - Design philosophy and patterns
- **[Project Summary](SUMMARY.md)** - Complete feature overview

## Features

- ✅ Fetches real-time weather data from multiple Weather Underground stations
- ✅ Transforms and forwards data to Windy.com
- ✅ Configurable sync intervals (default: 5 minutes)
- ✅ Automatic retry with exponential backoff
- ✅ Concurrent processing of multiple stations
- ✅ Health check endpoint for monitoring
- ✅ Structured logging
- ✅ Graceful shutdown handling
- ✅ Low resource usage (<128MB memory, <0.5 CPU cores)

## Architecture

Built using functional composition (no OOP), following DRY and KISS principles:

- **config.py**: Configuration loading from environment variables
- **wu_client.py**: Weather Underground API client
- **transformer.py**: Data transformation (WU → Windy format)
- **windy_client.py**: Windy API client
- **orchestrator.py**: Sync orchestration with concurrency control
- **scheduler.py**: Task scheduling
- **health.py**: Health check HTTP endpoint
- **retry.py**: Retry logic with exponential backoff

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
uv run pytest
```

### Run linting

```bash
uv run ruff check src/
```

### Run type checking

```bash
uv run mypy src/
```

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
- **[layereddsl.yml](layereddsl.yml)** - Formal architecture specification

## Author

Weather Data Integration Team
