# Architecture Documentation

## Design Philosophy

This application follows **functional composition** principles instead of object-oriented programming, adhering to DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles.

## Core Principles

### 1. Functional Composition

- Functions as the primary unit of organization
- Pure functions where possible
- Explicit dependencies passed as parameters
- No hidden state or side effects

### 2. DRY (Don't Repeat Yourself)

- Reusable functions across modules
- Configuration centralized in one place
- Common patterns extracted (retry logic, error handling)

### 3. KISS (Keep It Simple, Stupid)

- Straightforward data flow
- Minimal abstractions
- Clear function signatures
- Direct error handling

## Module Organization

```
weatherstationdatabridge/
├── models.py          # Domain models and exceptions
├── config.py          # Configuration loading
├── wu_client.py       # Weather Underground API
├── transformer.py     # Data transformation
├── windy_client.py    # Windy API
├── retry.py           # Retry logic
├── orchestrator.py    # Sync orchestration
├── scheduler.py       # Task scheduling
├── health.py          # Health monitoring
└── __init__.py        # CLI entry point
```

## Data Flow

```
1. Configuration Loading (config.py)
   └─> Environment Variables → Configuration object

2. Scheduler Loop (scheduler.py)
   └─> Every N minutes → Execute Sync Cycle

3. Sync Cycle (orchestrator.py)
   ├─> For each station (concurrent, max 2):
   │   ├─> Fetch WU Data (wu_client.py)
   │   ├─> Transform Data (transformer.py)
   │   └─> Send to Windy with Retry (windy_client.py + retry.py)
   └─> Return Sync Results

4. Health Monitoring (health.py)
   └─> HTTP endpoint → Check last sync status
```

## Function Composition Example

Instead of classes with methods, we compose functions:

```python
# Configuration
config = load_configuration()

# Create specialized functions
sync_executor = create_sync_executor(config)

# Compose into scheduler
run_scheduler(sync_executor, config.sync_interval_minutes)
```

## Error Handling Strategy

### Layered Error Handling

1. **API Client Level**: Raise specific exceptions

   - `APIConnectionError`
   - `AuthenticationError`
   - `StationNotFound`
   - `RateLimitExceeded`

2. **Retry Level**: Handle transient errors

   - Exponential backoff
   - Max attempts limit
   - Raises `MaxRetriesExceeded`

3. **Orchestrator Level**: Catch all errors

   - Continue on single station failure
   - Log errors
   - Return `SyncResult` with error details

4. **Scheduler Level**: Keep running
   - Log exceptions
   - Wait before retry
   - Never crash service

## Concurrency Model

### AsyncIO for I/O Operations

```python
async def sync_station(...):
    # Fetch (I/O bound)
    observation = fetch_weather_underground_data(...)

    # Transform (CPU bound, but fast)
    windy_obs = transform_to_windy_format(...)

    # Send with retry (I/O bound)
    await retry_with_backoff(...)
```

### Semaphore for Rate Limiting

```python
semaphore = asyncio.Semaphore(2)  # Max 2 concurrent

async def sync_with_semaphore(...):
    async with semaphore:
        return await sync_station(...)
```

## Configuration as Code

All behavior controlled by environment variables:

```python
config = Configuration(
    windy_api_key="...",
    wu_api_key="...",
    wu_station_ids=["KSTATION1", "KSTATION2"],
    windy_station_ids=["0", "1"],
    sync_interval_minutes=5,
    retry_attempts=3,
    retry_delay_seconds=5,
)
```

## Testing Strategy

### Unit Tests

- Test individual functions
- Mock external dependencies
- Test error conditions

### Integration Tests

- Use `test-sync` command
- Test with real (or mocked) APIs
- Verify end-to-end flow

## Performance Characteristics

### Memory Usage

- Minimal state storage
- Streaming data processing
- Station metadata cached
- **Target**: <128MB

### CPU Usage

- Mostly I/O bound (network)
- Async prevents blocking
- Idle between syncs
- **Target**: <0.5 cores

### Network

- Connection pooling (httpx)
- Concurrent requests (asyncio)
- Automatic retries
- **Target**: <1MB/min total

## Deployment Considerations

### Docker Container

- Python 3.11 slim base
- UV for fast dependency install
- Health check on port 8080
- Graceful shutdown handling

### Environment Variables

- All configuration via ENV
- No files to mount (except logs)
- Secrets in ENV (not in code)

### Monitoring

- Health check endpoint
- Structured logging
- Sync result tracking

## Extension Points

### Adding New Data Sources

1. Create new client module (e.g., `accuweather_client.py`)
2. Implement fetch function
3. Add to orchestrator

### Adding New Destinations

1. Create new client module (e.g., `weatherapi_client.py`)
2. Implement send function
3. Add to orchestrator

### Custom Transformations

1. Add transformer function
2. Compose in orchestrator
3. Test with unit tests

## Why No OOP?

### Problems with OOP for this use case:

- **Unnecessary abstraction**: No complex state to encapsulate
- **Hidden dependencies**: Methods access instance variables
- **Testing complexity**: Mocking objects harder than functions
- **Cognitive overhead**: Understanding class hierarchies

### Benefits of functional approach:

- **Explicit dependencies**: All inputs are parameters
- **Easy testing**: Mock functions, not objects
- **Simple composition**: Functions compose naturally
- **Clear data flow**: Input → Transform → Output

## Comparison

### OOP Approach (What we avoided)

```python
class WeatherSyncService:
    def __init__(self, config):
        self.config = config
        self.wu_client = WUClient(config.wu_api_key)
        self.windy_client = WindyClient(config.windy_api_key)

    def sync_station(self, station_id):
        # Hidden dependencies on self.config, self.wu_client, etc.
        pass
```

### Functional Approach (What we use)

```python
def sync_station(station_id, wu_api_key, windy_api_key, ...):
    # All dependencies explicit as parameters
    observation = fetch_weather_underground_data(wu_api_key, station_id)
    windy_obs = transform_to_windy_format(observation, ...)
    send_to_windy(windy_api_key, windy_obs)
```

## Conclusion

This architecture achieves:

- ✅ **Simplicity**: Easy to understand and modify
- ✅ **Testability**: Pure functions are easy to test
- ✅ **Reliability**: Explicit error handling at every level
- ✅ **Performance**: Async I/O with controlled concurrency
- ✅ **Maintainability**: Small, focused modules
- ✅ **Deployability**: Containerized with health checks
