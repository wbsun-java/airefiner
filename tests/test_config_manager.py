"""
Unit tests for configuration manager.
"""

import os
from unittest.mock import patch, MagicMock

import pytest

from config.config_manager import (
    APIConfiguration,
    ModelFilteringConfiguration,
    TasksConfiguration,
    ApplicationConfiguration,
    ConfigurationManager
)
from config.constants import ModelProvider, TaskConfiguration


class TestAPIConfiguration:
    """Test cases for APIConfiguration."""

    def test_from_environment_with_all_keys(self):
        """Test creating configuration from environment with all API keys."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai',
            'ANTHROPIC_API_KEY': 'sk-test-anthropic',
            'GOOGLE_API_KEY': 'test-google',
            'GROQ_API_KEY': 'gsk-test-groq',
            'XAI_API_KEY': 'xai-test'
        }):
            config = APIConfiguration.from_environment()

            assert config.openai_key == 'sk-test-openai'
            assert config.anthropic_key == 'sk-test-anthropic'
            assert config.google_key == 'test-google'
            assert config.groq_key == 'gsk-test-groq'
            assert config.xai_key == 'xai-test'

    def test_from_environment_with_partial_keys(self):
        """Test creating configuration with only some API keys."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai',
            'GOOGLE_API_KEY': 'test-google'
        }, clear=True):
            config = APIConfiguration.from_environment()

            assert config.openai_key == 'sk-test-openai'
            assert config.google_key == 'test-google'
            assert config.anthropic_key is None
            assert config.groq_key is None
            assert config.xai_key is None

    def test_get_api_keys_filters_none_values(self):
        """Test that get_api_keys filters out None values."""
        config = APIConfiguration(
            openai_key='sk-test',
            anthropic_key=None,
            google_key='test-google'
        )

        keys = config.get_api_keys()
        expected = {
            ModelProvider.OPENAI.value: 'sk-test',
            ModelProvider.GOOGLE.value: 'test-google'
        }

        assert keys == expected

    def test_validate_with_valid_keys(self):
        """Test validation with valid API keys."""
        config = APIConfiguration(
            openai_key='sk-test-openai-key-1234567890',
            google_key='test-google-key-1234567890'
        )

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_with_no_keys(self):
        """Test validation with no API keys."""
        config = APIConfiguration()

        errors = config.validate()
        assert 'At least one API key must be provided' in errors

    def test_validate_with_short_keys(self):
        """Test validation with keys that are too short."""
        config = APIConfiguration(openai_key='short')

        errors = config.validate()
        assert any('too short' in error for error in errors)

    def test_validate_with_empty_keys(self):
        """Test validation with empty keys."""
        config = APIConfiguration(openai_key='   ')

        errors = config.validate()
        assert any('empty' in error for error in errors)

    def test_get_available_providers(self):
        """Test getting available providers."""
        config = APIConfiguration(
            openai_key='sk-test',
            google_key='test-google'
        )

        providers = config.get_available_providers()
        expected = [ModelProvider.OPENAI.value, ModelProvider.GOOGLE.value]

        assert set(providers) == set(expected)


class TestModelFilteringConfiguration:
    """Test cases for ModelFilteringConfiguration."""

    def test_default_configuration(self):
        """Test default filtering configuration."""
        config = ModelFilteringConfiguration()

        assert config.enable_strict_filtering is True
        assert config.custom_exclude_keywords == []

    def test_validate_with_valid_keywords(self):
        """Test validation with valid string keywords."""
        config = ModelFilteringConfiguration(
            custom_exclude_keywords=['keyword1', 'keyword2']
        )

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_with_invalid_keywords(self):
        """Test validation with non-string keywords."""
        config = ModelFilteringConfiguration(
            custom_exclude_keywords=['valid', 123, None]
        )

        errors = config.validate()
        assert len(errors) == 2  # 123 and None are invalid


class TestTasksConfiguration:
    """Test cases for TasksConfiguration."""

    def test_default_configuration(self):
        """Test default tasks configuration."""
        config = TasksConfiguration()

        assert len(config.tasks) == 3
        assert "1" in config.tasks
        assert config.tasks["1"]["id"] == TaskConfiguration.REFINE

    def test_validate_with_valid_tasks(self):
        """Test validation with valid task configuration."""
        config = TasksConfiguration()

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_with_missing_id(self):
        """Test validation with task missing ID."""
        config = TasksConfiguration(tasks={
            "1": {"name": "Test Task"}
        })

        errors = config.validate()
        assert any("missing required 'id' field" in error for error in errors)

    def test_validate_with_missing_name(self):
        """Test validation with task missing name."""
        config = TasksConfiguration(tasks={
            "1": {"id": "test"}
        })

        errors = config.validate()
        assert any("missing required 'name' field" in error for error in errors)

    def test_validate_with_unknown_task_id(self):
        """Test validation with unknown task ID."""
        config = TasksConfiguration(tasks={
            "1": {"id": "unknown_task", "name": "Unknown Task"}
        })

        errors = config.validate()
        assert any("unknown task ID" in error for error in errors)

    def test_get_task_by_id_existing(self):
        """Test getting existing task by ID."""
        config = TasksConfiguration()

        task = config.get_task_by_id(TaskConfiguration.REFINE)
        assert task is not None
        assert task["id"] == TaskConfiguration.REFINE

    def test_get_task_by_id_nonexistent(self):
        """Test getting non-existent task by ID."""
        config = TasksConfiguration()

        task = config.get_task_by_id("nonexistent")
        assert task is None


class TestApplicationConfiguration:
    """Test cases for ApplicationConfiguration."""

    def test_validate_with_valid_config(self):
        """Test validation with valid configuration."""
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(api_config=api_config)

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_with_invalid_temperature(self):
        """Test validation with invalid temperature."""
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(
            api_config=api_config,
            default_temperature=3.0  # Invalid, should be <= 2.0
        )

        errors = config.validate()
        assert any("temperature must be between" in error for error in errors)

    def test_validate_with_invalid_log_level(self):
        """Test validation with invalid log level."""
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(
            api_config=api_config,
            log_level="INVALID"
        )

        errors = config.validate()
        assert any("Log level must be one of" in error for error in errors)

    def test_is_valid_true(self):
        """Test is_valid returns True for valid configuration."""
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(api_config=api_config)

        assert config.is_valid() is True

    def test_is_valid_false(self):
        """Test is_valid returns False for invalid configuration."""
        api_config = APIConfiguration()  # No API keys
        config = ApplicationConfiguration(api_config=api_config)

        assert config.is_valid() is False


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def test_load_configuration_success(self):
        """Test successful configuration loading."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai-key-1234567890',
            'LOG_LEVEL': 'DEBUG'
        }):
            manager = ConfigurationManager()

            config = manager.load_configuration()

            assert config.api_config.openai_key == 'sk-test-openai-key-1234567890'
            assert config.log_level == 'DEBUG'
            assert config.is_valid()

    def test_load_configuration_validation_error(self):
        """Test configuration loading with validation error."""
        with patch.dict(os.environ, {}, clear=True):
            manager = ConfigurationManager()

            with pytest.raises(ValueError, match="Configuration validation failed"):
                manager.load_configuration()

    def test_get_configuration_not_loaded(self):
        """Test getting configuration when not loaded."""
        manager = ConfigurationManager()

        with pytest.raises(RuntimeError, match="Configuration not loaded"):
            manager.get_configuration()

    def test_get_configuration_loaded(self):
        """Test getting configuration after loading."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai-key-1234567890'
        }):
            manager = ConfigurationManager()
            loaded_config = manager.load_configuration()

            retrieved_config = manager.get_configuration()
            assert retrieved_config is loaded_config

    @patch('config.config_manager.ConfigurationManager._log_configuration_summary')
    def test_log_configuration_summary_called(self, mock_log_summary):
        """Test that configuration summary is logged."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai-key-1234567890'
        }):
            manager = ConfigurationManager()
            config = manager.load_configuration()

            mock_log_summary.assert_called_once_with(config)


@pytest.fixture
def mock_config_manager():
    """Fixture for mocked configuration manager."""
    with patch('config.config_manager._config_manager') as mock:
        yield mock


def test_load_config_function(mock_config_manager):
    """Test global load_config function."""
    from config.config_manager import load_config

    mock_config = MagicMock()
    mock_config_manager.load_configuration.return_value = mock_config

    result = load_config()

    mock_config_manager.load_configuration.assert_called_once_with(None)
    assert result is mock_config


def test_get_config_function(mock_config_manager):
    """Test global get_config function."""
    from config.config_manager import get_config

    mock_config = MagicMock()
    mock_config_manager.get_configuration.return_value = mock_config

    result = get_config()

    mock_config_manager.get_configuration.assert_called_once()
    assert result is mock_config
