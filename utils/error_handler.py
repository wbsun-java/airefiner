"""
Centralized error handling for the AIRefiner project.
"""

import time
from typing import Any, Callable, Optional

from utils.logger import LoggerMixin

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = None


class AIRefinerError(Exception):
    """Base exception class for AIRefiner application."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class ModelInitializationError(AIRefinerError):
    """Raised when model initialization fails."""

    def __init__(self, message: str, model_key: str, original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.model_key = model_key


class APIError(AIRefinerError):
    """Raised when API calls fail."""

    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.provider = provider


class ProcessingError(AIRefinerError):
    """Raised when text processing fails."""

    def __init__(self, message: str, task_id: str, original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.task_id = task_id


class ErrorHandler(LoggerMixin):
    """Centralized error handling with logging."""

    def handle_error(self, error: Exception, context: str = "") -> str:
        log_message = f"{context}: {error}" if context else str(error)

        if isinstance(error, AIRefinerError):
            self.logger.error(log_message)
            if error.original_error:
                self.logger.debug("Original exception:", exc_info=error.original_error)
        else:
            self.logger.warning(log_message)

        return self._get_user_friendly_message(error)

    def _get_user_friendly_message(self, error: Exception) -> str:
        if isinstance(error, ProcessingError):
            return f"Processing error in task '{error.task_id}': {error.message}"
        elif isinstance(error, ModelInitializationError):
            return f"Failed to initialize model '{error.model_key}': {error.message}"
        elif isinstance(error, APIError):
            return f"API error with {error.provider}: {error.message}"

        if ResourceExhausted and isinstance(error, ResourceExhausted):
            return "Google API quota exceeded. Please wait and try again, or select a different model."

        if "429" in str(error) or "rate_limit_exceeded" in str(error).lower():
            return "API rate limit or quota exceeded. Please wait and try again, or select a different model."

        return f"An unexpected error occurred: {str(error)}"


class CircuitBreaker(LoggerMixin):
    """Circuit breaker pattern for failing operations."""

    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half-open"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0, name: str = "operation"):
        super().__init__()
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = self.STATE_CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        current_time = time.time()

        if (self.state == self.STATE_OPEN and self.last_failure_time and
                current_time - self.last_failure_time > self.recovery_timeout):
            self.state = self.STATE_HALF_OPEN
            self.logger.info(f"Circuit breaker for '{self.name}' entering half-open state")

        if self.state == self.STATE_OPEN:
            raise APIError(
                f"Circuit breaker is open for '{self.name}'. The model has failed repeatedly and is temporarily unavailable.",
                self.name
            )

        try:
            result = func(*args, **kwargs)
            if self.state == self.STATE_HALF_OPEN:
                self.state = self.STATE_CLOSED
                self.failure_count = 0
                self.logger.info(f"Circuit breaker for '{self.name}' reset to closed state")
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = current_time
            if self.failure_count >= self.failure_threshold:
                self.state = self.STATE_OPEN
                self.logger.error(
                    f"Circuit breaker opened for '{self.name}' after {self.failure_count} failures"
                )
            raise e


_error_handler = ErrorHandler()


def handle_error(error: Exception, context: str = "") -> str:
    return _error_handler.handle_error(error, context)
