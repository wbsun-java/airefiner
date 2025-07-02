"""
Centralized error handling patterns for the AIRefiner project.
"""

import functools
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from utils.logger import LoggerMixin


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIRefinerError(Exception):
    """Base exception class for AIRefiner application."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.original_error = original_error


class ConfigurationError(AIRefinerError):
    """Raised when there's a configuration problem."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorSeverity.HIGH, original_error)


class ModelInitializationError(AIRefinerError):
    """Raised when model initialization fails."""

    def __init__(self, message: str, model_key: str, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorSeverity.MEDIUM, original_error)
        self.model_key = model_key


class APIError(AIRefinerError):
    """Raised when API calls fail."""

    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorSeverity.MEDIUM, original_error)
        self.provider = provider


class ValidationError(AIRefinerError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorSeverity.MEDIUM, original_error)
        self.field = field


class ProcessingError(AIRefinerError):
    """Raised when text processing fails."""

    def __init__(self, message: str, task_id: str, original_error: Optional[Exception] = None):
        super().__init__(message, ErrorSeverity.MEDIUM, original_error)
        self.task_id = task_id


F = TypeVar('F', bound=Callable[..., Any])


class ErrorHandler(LoggerMixin):
    """Centralized error handling with logging and recovery strategies."""

    def __init__(self):
        super().__init__()

    def handle_error(self, error: Exception, context: str = "") -> str:
        """
        Handle an error with appropriate logging and return user-friendly message.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            User-friendly error message
        """
        # Determine error type and severity
        if isinstance(error, AIRefinerError):
            severity = error.severity
            message = error.message
            original_error = error.original_error
        else:
            severity = ErrorSeverity.MEDIUM
            message = str(error)
            original_error = error

        # Log based on severity
        log_message = f"{context}: {message}" if context else message

        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
            if original_error:
                self.logger.exception("Original exception:", exc_info=original_error)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
            if original_error:
                self.logger.exception("Original exception:", exc_info=original_error)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
            if original_error and self.logger.logger.level <= 10:  # DEBUG level
                self.logger.debug("Original exception details:", exc_info=original_error)
        else:  # LOW
            self.logger.info(log_message)

        # Return user-friendly message
        return self._get_user_friendly_message(error, context)

    def _get_user_friendly_message(self, error: Exception, context: str) -> str:
        """Generate user-friendly error message."""
        if isinstance(error, ConfigurationError):
            return f"Configuration error: {error.message}"
        elif isinstance(error, ModelInitializationError):
            return f"Failed to initialize model '{error.model_key}': {error.message}"
        elif isinstance(error, APIError):
            return f"API error with {error.provider}: {error.message}"
        elif isinstance(error, ValidationError):
            field_info = f" (field: {error.field})" if error.field else ""
            return f"Validation error{field_info}: {error.message}"
        elif isinstance(error, ProcessingError):
            return f"Processing error in task '{error.task_id}': {error.message}"
        else:
            return f"An unexpected error occurred: {str(error)}"


def with_error_handling(context: str = "", return_on_error: Any = None):
    """
    Decorator for automatic error handling.
    
    Args:
        context: Context description for logging
        return_on_error: Value to return if an error occurs
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = ErrorHandler()
                error_handler.handle_error(e, context or func.__name__)
                return return_on_error

        return wrapper

    return decorator


def safe_execute(func: Callable, *args, default_return: Any = None,
                 context: str = "", **kwargs) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments for the function
        default_return: Value to return on error
        context: Context for error logging
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler = ErrorHandler()
        error_handler.handle_error(e, context or func.__name__)
        return default_return


class RetryConfig:
    """Configuration for retry operations."""

    def __init__(self, max_attempts: int = 3, delay: float = 1.0,
                 backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions


def with_retry(config: RetryConfig):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        config: Retry configuration
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            delay = config.delay

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        error_handler = ErrorHandler()
                        error_handler.logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= config.backoff_factor
                    else:
                        error_handler = ErrorHandler()
                        error_handler.logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}"
                        )

            # Re-raise the last exception
            raise last_exception

        return wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for failing operations."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
        self.logger = LoggerMixin().logger

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        import time

        current_time = time.time()

        # Check if circuit should be reset
        if (self.state == "open" and self.last_failure_time and
                current_time - self.last_failure_time > self.recovery_timeout):
            self.state = "half-open"
            self.logger.info(f"Circuit breaker for {func.__name__} entering half-open state")

        # If circuit is open, fail immediately
        if self.state == "open":
            raise APIError(
                f"Circuit breaker is open for {func.__name__}",
                func.__name__
            )

        try:
            result = func(*args, **kwargs)

            # Success - reset circuit if it was half-open
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                self.logger.info(f"Circuit breaker for {func.__name__} reset to closed state")

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = current_time

            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                self.logger.error(
                    f"Circuit breaker opened for {func.__name__} after {self.failure_count} failures"
                )

            raise e


# Global error handler instance
_error_handler = ErrorHandler()


def handle_error(error: Exception, context: str = "") -> str:
    """
    Global error handling function.
    
    Args:
        error: Exception to handle
        context: Context information
        
    Returns:
        User-friendly error message
    """
    return _error_handler.handle_error(error, context)
