"""
Unit tests for error handling system.
"""

import time
from unittest.mock import patch

import pytest

from utils.error_handler import (
    ErrorSeverity,
    AIRefinerError,
    ConfigurationError,
    ModelInitializationError,
    APIError,
    ValidationError,
    ProcessingError,
    ErrorHandler,
    with_error_handling,
    safe_execute,
    RetryConfig,
    with_retry,
    CircuitBreaker,
    handle_error
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_airefiner_error_default_severity(self):
        """Test AIRefinerError with default severity."""
        error = AIRefinerError("Test error")

        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.original_error is None

    def test_airefiner_error_with_original(self):
        """Test AIRefinerError with original error."""
        original = ValueError("Original error")
        error = AIRefinerError("Test error", ErrorSeverity.HIGH, original)

        assert error.severity == ErrorSeverity.HIGH
        assert error.original_error is original

    def test_configuration_error_has_high_severity(self):
        """Test ConfigurationError has high severity by default."""
        error = ConfigurationError("Config error")

        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Config error"

    def test_model_initialization_error_has_model_key(self):
        """Test ModelInitializationError stores model key."""
        error = ModelInitializationError("Init failed", "test-model")

        assert error.model_key == "test-model"
        assert error.severity == ErrorSeverity.MEDIUM

    def test_api_error_has_provider(self):
        """Test APIError stores provider."""
        error = APIError("API failed", "openai")

        assert error.provider == "openai"
        assert error.severity == ErrorSeverity.MEDIUM

    def test_validation_error_has_field(self):
        """Test ValidationError stores field."""
        error = ValidationError("Invalid value", "username")

        assert error.field == "username"
        assert error.severity == ErrorSeverity.MEDIUM

    def test_processing_error_has_task_id(self):
        """Test ProcessingError stores task ID."""
        error = ProcessingError("Processing failed", "refine")

        assert error.task_id == "refine"
        assert error.severity == ErrorSeverity.MEDIUM


class TestErrorHandler:
    """Test ErrorHandler class."""

    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing."""
        return ErrorHandler()

    def test_handle_airefiner_error_critical(self, error_handler):
        """Test handling critical AIRefiner error."""
        original = ValueError("Original")
        error = ConfigurationError("Config failed", original)

        with patch.object(error_handler.logger, 'error') as mock_error, \
                patch.object(error_handler.logger, 'exception') as mock_exception:
            result = error_handler.handle_error(error, "test context")

            mock_error.assert_called_once()
            mock_exception.assert_called_once()
            assert "Configuration error: Config failed" in result

    def test_handle_standard_exception(self, error_handler):
        """Test handling standard Python exception."""
        error = ValueError("Standard error")

        with patch.object(error_handler.logger, 'warning') as mock_warning:
            result = error_handler.handle_error(error, "test context")

            mock_warning.assert_called_once_with("test context: Standard error")
            assert "An unexpected error occurred: Standard error" in result

    def test_handle_error_without_context(self, error_handler):
        """Test handling error without context."""
        error = ValidationError("Validation failed")

        with patch.object(error_handler.logger, 'warning') as mock_warning:
            result = error_handler.handle_error(error)

            mock_warning.assert_called_once_with("Validation failed")
            assert "Validation error: Validation failed" in result

    def test_get_user_friendly_message_model_error(self, error_handler):
        """Test user-friendly message for model error."""
        error = ModelInitializationError("Init failed", "gpt-4")

        result = error_handler._get_user_friendly_message(error, "")

        assert "Failed to initialize model 'gpt-4': Init failed" in result

    def test_get_user_friendly_message_api_error(self, error_handler):
        """Test user-friendly message for API error."""
        error = APIError("Rate limit exceeded", "openai")

        result = error_handler._get_user_friendly_message(error, "")

        assert "API error with openai: Rate limit exceeded" in result

    def test_get_user_friendly_message_validation_error_with_field(self, error_handler):
        """Test user-friendly message for validation error with field."""
        error = ValidationError("Invalid format", "email")

        result = error_handler._get_user_friendly_message(error, "")

        assert "Validation error (field: email): Invalid format" in result

    def test_get_user_friendly_message_processing_error(self, error_handler):
        """Test user-friendly message for processing error."""
        error = ProcessingError("Model failed", "translate")

        result = error_handler._get_user_friendly_message(error, "")

        assert "Processing error in task 'translate': Model failed" in result


class TestErrorHandlingDecorator:
    """Test error handling decorator."""

    def test_with_error_handling_success(self):
        """Test decorator when function succeeds."""

        @with_error_handling("test context", "error_return")
        def test_function(x):
            return x * 2

        result = test_function(5)
        assert result == 10

    def test_with_error_handling_exception(self):
        """Test decorator when function raises exception."""

        @with_error_handling("test context", "error_return")
        def test_function():
            raise ValueError("Test error")

        with patch('utils.error_handler.ErrorHandler') as mock_handler_class:
            mock_handler = mock_handler_class.return_value

            result = test_function()

            assert result == "error_return"
            mock_handler.handle_error.assert_called_once()

    def test_with_error_handling_no_return_value(self):
        """Test decorator with no return value specified."""

        @with_error_handling("test context")
        def test_function():
            raise ValueError("Test error")

        with patch('utils.error_handler.ErrorHandler'):
            result = test_function()
            assert result is None


class TestSafeExecute:
    """Test safe_execute function."""

    def test_safe_execute_success(self):
        """Test safe_execute when function succeeds."""

        def test_func(x, y):
            return x + y

        result = safe_execute(test_func, 2, 3)
        assert result == 5

    def test_safe_execute_exception(self):
        """Test safe_execute when function raises exception."""

        def test_func():
            raise ValueError("Test error")

        with patch('utils.error_handler.ErrorHandler') as mock_handler_class:
            result = safe_execute(test_func, default_return="default")

            assert result == "default"
            mock_handler_class.return_value.handle_error.assert_called_once()

    def test_safe_execute_with_kwargs(self):
        """Test safe_execute with keyword arguments."""

        def test_func(x, y=10):
            return x * y

        result = safe_execute(test_func, 3, y=4)
        assert result == 12


class TestRetryDecorator:
    """Test retry decorator."""

    def test_with_retry_success_first_attempt(self):
        """Test retry decorator when function succeeds on first attempt."""
        config = RetryConfig(max_attempts=3, delay=0.1)

        @with_retry(config)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_with_retry_success_after_failures(self):
        """Test retry decorator when function succeeds after failures."""
        config = RetryConfig(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        call_count = 0

        @with_retry(config)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        with patch('utils.error_handler.ErrorHandler'):
            result = test_function()

            assert result == "success"
            assert call_count == 3

    def test_with_retry_all_attempts_fail(self):
        """Test retry decorator when all attempts fail."""
        config = RetryConfig(max_attempts=2, delay=0.01)

        @with_retry(config)
        def test_function():
            raise ValueError("Persistent failure")

        with patch('utils.error_handler.ErrorHandler'), \
                pytest.raises(ValueError, match="Persistent failure"):
            test_function()

    def test_with_retry_non_retryable_exception(self):
        """Test retry decorator with non-retryable exception."""
        config = RetryConfig(max_attempts=3, exceptions=(ValueError,))

        @with_retry(config)
        def test_function():
            raise TypeError("Non-retryable")

        with pytest.raises(TypeError, match="Non-retryable"):
            test_function()


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_circuit_breaker_closed_state_success(self):
        """Test circuit breaker in closed state with successful calls."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        def test_func():
            return "success"

        result = breaker.call(test_func)
        assert result == "success"
        assert breaker.state == "closed"

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        def failing_func():
            raise ValueError("Failure")

        # First failure
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "closed"

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "open"

    def test_circuit_breaker_open_state_fails_immediately(self):
        """Test circuit breaker in open state fails immediately."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1.0)

        def failing_func():
            raise ValueError("Failure")

        # Trigger circuit to open
        with pytest.raises(ValueError):
            breaker.call(failing_func)

        # Next call should fail immediately with APIError
        with pytest.raises(APIError, match="Circuit breaker is open"):
            breaker.call(failing_func)

    def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker transitions to half-open state."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        def failing_func():
            raise ValueError("Failure")

        # Open the circuit
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "open"

        # Wait for recovery timeout
        time.sleep(0.02)

        # Next call should transition to half-open
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        # State should still be open after failure in half-open
        assert breaker.state == "open"

    def test_circuit_breaker_reset_after_success_in_half_open(self):
        """Test circuit breaker resets after success in half-open state."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        def test_func():
            return "success"

        def failing_func():
            raise ValueError("Failure")

        # Open the circuit
        with pytest.raises(ValueError):
            breaker.call(failing_func)

        # Wait for recovery timeout
        time.sleep(0.02)

        # Successful call should reset circuit
        result = breaker.call(test_func)
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0


class TestGlobalErrorHandler:
    """Test global error handling function."""

    def test_global_handle_error(self):
        """Test global handle_error function."""
        error = ValidationError("Test error")

        with patch('utils.error_handler._error_handler') as mock_handler:
            mock_handler.handle_error.return_value = "handled"

            result = handle_error(error, "test context")

            mock_handler.handle_error.assert_called_once_with(error, "test context")
            assert result == "handled"
