# Quick Start Guide

Get up and running with Weather Station Data Bridge in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- UV package manager ([install instructions](https://github.com/astral-sh/uv))
- Weather Underground API key
- Windy API key

## Step 1: Install UV (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Step 2: Clone and Setup

```bash
# Clone the repository
cd WeatherStationDataBridge

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
```

## Step 3: Configure

Edit `.env` and add your credentials:

```env
# Required
WINDY_API_KEY=your_windy_api_key_here
WU_API_KEY=your_wu_api_key_here
WU_STATION_IDS=KSTATION1,KSTATION2,KSTATION3
WINDY_STATION_IDS=0,1,2

# Optional (defaults shown)
SYNC_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5
```

**Note**: `WINDY_STATION_IDS` must match the order of `WU_STATION_IDS`. Find your Windy station IDs at https://stations.windy.com/ (shown as "Station ID: N" for each station).

## Step 4: Test

Run a single sync cycle to verify everything works:

```bash
uv run weatherstationdatabridge test-sync
```

Expected output:

```
Running test sync cycle
...
Sync Results:
============================================================
✓ KSTATION1: SUCCESS
✓ KSTATION2: SUCCESS
✓ KSTATION3: SUCCESS
============================================================
Total: 3/3 successful
```

## Step 5: Run

Start the service:

```bash
uv run weatherstationdatabridge run
```

The service will:

- Sync data every 5 minutes (configurable)
- Expose health check on http://localhost:8080/health
- Log all operations to stdout

## Health Check

Verify the service is running:

```bash
curl http://localhost:8080/health
```

Response: `OK: Last sync 30s ago`

## Troubleshooting

### Authentication Errors

```
Error: Invalid Weather Underground API key
```

**Solution**: Verify your `WU_API_KEY` in `.env`

### Station Not Found

```
Error: Station KTEST123 not found
```

**Solution**: Check station IDs at https://www.wunderground.com/pws/overview

### Rate Limit Exceeded

```
Error: Rate limit exceeded for Weather Underground API
```

**Solution**: Increase `SYNC_INTERVAL_MINUTES` or reduce number of stations

### Connection Errors

```
Error: Timeout connecting to Weather Underground API
```

**Solution**: Check internet connection, verify API endpoints are accessible

## Next Steps

- **Docker Deployment**: See `Dockerfile` for containerized deployment
- **Monitoring**: Use the health check endpoint with your monitoring system
- **Testing**: Run `uv run pytest` to execute test suite
- **Development**: See README.md for development setup

## Getting API Keys

### Weather Underground

1. Visit https://www.wunderground.com/member/api-keys
2. Sign up or log in
3. Create a new API key

### Windy

1. Visit https://stations.windy.com/
2. Register as a station owner
3. Get your API key from the dashboard

## Support

For issues or questions:

- Check the main README.md
- Review error logs with `LOG_LEVEL=DEBUG`
- Verify API endpoints are accessible
