FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files (include README.md required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose health check port
EXPOSE 8080

# Run the service
CMD ["uv", "run", "weatherstationdatabridge", "run"]
