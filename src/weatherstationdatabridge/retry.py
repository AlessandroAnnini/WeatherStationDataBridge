"""Retry logic with exponential backoff."""

import asyncio
import logging
from typing import Callable, TypeVar

from .models import MaxRetriesExceeded

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    operation: Callable[[], T],
    max_attempts: int,
    delay_seconds: float,
    operation_name: str = "operation",
) -> T:
    """
    Retry an operation with exponential backoff.

    Args:
        operation: Callable to retry
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries in seconds
        operation_name: Name of the operation for logging

    Returns:
        Result of the operation

    Raises:
        MaxRetriesExceeded: If max attempts exceeded
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(
                f"Attempting {operation_name} (attempt {attempt}/{max_attempts})"
            )
            return operation()
        except Exception as e:
            last_exception = e
            logger.warning(
                f"{operation_name} failed (attempt {attempt}/{max_attempts}): {e}"
            )

            if attempt < max_attempts:
                wait_time = delay_seconds * (2 ** (attempt - 1))
                logger.debug(f"Waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

    raise MaxRetriesExceeded(
        f"{operation_name} failed after {max_attempts} attempts: {last_exception}"
    ) from last_exception
