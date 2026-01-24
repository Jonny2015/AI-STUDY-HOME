"""Retry logic with exponential backoff for transient failures.

This module provides retry mechanisms for handling transient failures in
LLM calls and database operations. It implements exponential backoff
with jitter to avoid thundering herd problems.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pg_mcp.models.errors import PgMcpError

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (including initial attempt).
            base_delay: Initial delay in seconds before first retry.
            max_delay: Maximum delay in seconds between retries.
            backoff_factor: Multiplier for exponential backoff.
            jitter: Whether to add random jitter to delays.
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    config: RetryConfig,
    retryable_errors: tuple[type[Exception], ...] | None = None,
) -> T:
    """Execute an async function with retry and exponential backoff.

    This function implements exponential backoff with jitter to handle
    transient failures gracefully. It's particularly useful for LLM API calls
    and database operations that may fail temporarily.

    Args:
        func: Async function to execute.
        config: Retry configuration.
        retryable_errors: Tuple of exception types that should trigger retry.
            If None, all exceptions are retried.

    Returns:
        The result of the function call.

    Raises:
        The last exception if all retry attempts are exhausted.

    Examples:
        >>> config = RetryConfig(max_attempts=3, base_delay=1.0)
        >>> result = await retry_with_backoff(
        ...     func=lambda: api_call(),
        ...     config=config,
        ...     retryable_errors=(TimeoutError, ConnectionError),
        ... )
    """
    last_exception: Exception | None = None

    for attempt in range(config.max_attempts):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            # Check if this error type should be retried
            if retryable_errors and not isinstance(e, retryable_errors):
                raise

            # If this is the last attempt, don't wait
            if attempt == config.max_attempts - 1:
                break

            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.backoff_factor ** attempt),
                config.max_delay,
            )

            # Add jitter to avoid thundering herd
            if config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)

            # Wait before retry
            await asyncio.sleep(delay)

    # All attempts exhausted
    if last_exception is not None:
        raise last_exception

    # Should never reach here, but just in case
    raise RuntimeError("Retry logic failed unexpectedly")


class RetryableError(PgMcpError):
    """Base class for errors that should trigger retry logic.

    Exceptions inheriting from this class are considered transient
    and suitable for automatic retry with backoff.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, any] | None = None,
    ) -> None:
        """Initialize retryable error.

        Args:
            message: Error message.
            details: Optional error details.
        """
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_ERROR,
            details=details,
        )


# Import ErrorCode at module level to avoid circular dependency
from pg_mcp.models.errors import ErrorCode
