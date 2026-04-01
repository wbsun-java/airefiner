"""
Unit tests for error handling system.
"""

import time
from unittest.mock import patch

import pytest

from utils.error_handler import (
    AIRefinerError,
    ModelInitializationError,
    APIError,
    ProcessingError,
    ErrorHandler,
    CircuitBreaker,
    handle_error
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_airefiner_error_defaults(self):
        error = AIRefinerError("Test error")
        assert error.message == "Test error"
        assert error.original_error is None

    def test_airefiner_error_with_original(self):
        original = ValueError("Original error")
        error = AIRefinerError("Test error", original)
        assert error.original_error is original

    def test_model_initialization_error_has_model_key(self):
        error = ModelInitializationError("Init failed", "test-model")
        assert error.model_key == "test-model"

    def test_api_error_has_provider(self):
        error = APIError("API failed", "openai")
        assert error.provider == "openai"

    def test_processing_error_has_task_id(self):
        error = ProcessingError("Processing failed", "refine")
        assert error.task_id == "refine"


class TestErrorHandler:
    """Test ErrorHandler class."""

    @pytest.fixture
    def error_handler(self):
        return ErrorHandler()

    def test_handle_airefiner_error(self, error_handler):
        original = ValueError("Original")
        error = ModelInitializationError("Init failed", "gpt-4", original)

        with patch.object(error_handler.logger, 'error') as mock_error:
            result = error_handler.handle_error(error, "test context")
            mock_error.assert_called_once()
            assert "Failed to initialize model 'gpt-4': Init failed" in result

    def test_handle_standard_exception(self, error_handler):
        error = ValueError("Standard error")

        with patch.object(error_handler.logger, 'warning') as mock_warning:
            result = error_handler.handle_error(error, "test context")
            mock_warning.assert_called_once_with("test context: Standard error")
            assert "An unexpected error occurred: Standard error" in result

    def test_handle_error_without_context(self, error_handler):
        error = ProcessingError("Processing failed", "refine")

        with patch.object(error_handler.logger, 'error'):
            result = error_handler.handle_error(error)
            assert "Processing error in task 'refine': Processing failed" in result

    def test_get_user_friendly_message_model_error(self, error_handler):
        error = ModelInitializationError("Init failed", "gpt-4")
        result = error_handler._get_user_friendly_message(error)
        assert "Failed to initialize model 'gpt-4': Init failed" in result

    def test_get_user_friendly_message_api_error(self, error_handler):
        error = APIError("Rate limit exceeded", "openai")
        result = error_handler._get_user_friendly_message(error)
        assert "API error with openai: Rate limit exceeded" in result

    def test_get_user_friendly_message_processing_error(self, error_handler):
        error = ProcessingError("Model failed", "translate")
        result = error_handler._get_user_friendly_message(error)
        assert "Processing error in task 'translate': Model failed" in result


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_circuit_breaker_closed_state_success(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == "closed"

    def test_circuit_breaker_opens_after_failures(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        def failing_func():
            raise ValueError("Failure")

        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "closed"

        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "open"

    def test_circuit_breaker_open_state_fails_immediately(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1.0)

        def failing_func():
            raise ValueError("Failure")

        with pytest.raises(ValueError):
            breaker.call(failing_func)

        with pytest.raises(APIError, match="Circuit breaker is open"):
            breaker.call(failing_func)

    def test_circuit_breaker_half_open_state(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        def failing_func():
            raise ValueError("Failure")

        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "open"

        time.sleep(0.02)

        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker.state == "open"

    def test_circuit_breaker_reset_after_success_in_half_open(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        def failing_func():
            raise ValueError("Failure")

        with pytest.raises(ValueError):
            breaker.call(failing_func)

        time.sleep(0.02)

        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0


class TestGlobalErrorHandler:
    """Test global error handling function."""

    def test_global_handle_error(self):
        error = ProcessingError("Test error", "refine")

        with patch('utils.error_handler._error_handler') as mock_handler:
            mock_handler.handle_error.return_value = "handled"
            result = handle_error(error, "test context")
            mock_handler.handle_error.assert_called_once_with(error, "test context")
            assert result == "handled"
