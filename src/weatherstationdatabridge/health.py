"""Health check endpoint."""

import asyncio
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

logger = logging.getLogger(__name__)

# Global health status
_last_sync_time: Optional[datetime] = None
_last_sync_success: bool = False


def update_health_status(success: bool) -> None:
    """
    Update the health status.

    Args:
        success: Whether the last sync was successful
    """
    global _last_sync_time, _last_sync_success
    _last_sync_time = datetime.now()
    _last_sync_success = success


def get_health_status() -> tuple[bool, str]:
    """
    Get the current health status.

    Returns:
        Tuple of (healthy, message)
    """
    if _last_sync_time is None:
        return True, "Service starting, no sync yet"

    time_since_sync = (datetime.now() - _last_sync_time).total_seconds()

    # Consider unhealthy if no successful sync in last 15 minutes
    if time_since_sync > 900 and not _last_sync_success:
        return False, f"No successful sync in {int(time_since_sync)}s"

    return True, f"Last sync {int(time_since_sync)}s ago"


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks."""

    def do_GET(self) -> None:
        """Handle GET request."""
        if self.path == "/health":
            healthy, message = get_health_status()

            if healthy:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"OK: {message}\n".encode())
            else:
                self.send_response(503)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"UNHEALTHY: {message}\n".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


async def run_health_server(port: int = 8080) -> None:
    """
    Run the health check HTTP server.

    Args:
        port: Port to listen on
    """
    server = HTTPServer(("127.0.0.1", port), HealthCheckHandler)
    logger.info(f"Health check server listening on port {port}")

    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, server.serve_forever)
