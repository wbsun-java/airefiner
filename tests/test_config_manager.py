"""
Unit tests for configuration manager.
"""

import os
from unittest.mock import patch, MagicMock

import pytest

from config.config_manager import (
    APIConfiguration,
    ApplicationConfiguration,
    load_config,
    get_config,
    TASKS,
)
from config.constants import ModelProvider, TaskConfiguration


class TestAPIConfiguration:
    """Test cases for APIConfiguration."""

    def test_from_environment_with_all_keys(self):
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
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai',
            'GOOGLE_API_KEY': 'test-google'
        }, clear=True):
            config = APIConfiguration.from_environment()
            assert config.openai_key == 'sk-test-openai'
            assert config.google_key == 'test-google'
            assert config.anthropic_key is None

    def test_get_api_keys_filters_none_values(self):
        config = APIConfiguration(openai_key='sk-test', google_key='test-google')
        keys = config.get_api_keys()
        assert ModelProvider.OPENAI.value in keys
        assert ModelProvider.GOOGLE.value in keys
        assert ModelProvider.ANTHROPIC.value not in keys

    def test_validate_with_valid_keys(self):
        config = APIConfiguration(openai_key='sk-test-openai-key-1234567890')
        assert len(config.validate()) == 0

    def test_validate_with_no_keys(self):
        config = APIConfiguration()
        errors = config.validate()
        assert 'At least one API key must be provided' in errors

    def test_validate_with_short_keys(self):
        config = APIConfiguration(openai_key='short')
        errors = config.validate()
        assert any('too short' in e for e in errors)

    def test_validate_with_empty_keys(self):
        config = APIConfiguration(openai_key='   ')
        errors = config.validate()
        assert any('empty' in e for e in errors)

    def test_get_available_providers(self):
        config = APIConfiguration(openai_key='sk-test', google_key='test-google')
        providers = config.get_available_providers()
        assert set(providers) == {ModelProvider.OPENAI.value, ModelProvider.GOOGLE.value}


class TestApplicationConfiguration:
    """Test cases for ApplicationConfiguration."""

    def test_validate_with_valid_config(self):
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(api_config=api_config)
        assert len(config.validate()) == 0

    def test_validate_with_invalid_temperature(self):
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(api_config=api_config, default_temperature=3.0)
        errors = config.validate()
        assert any("temperature must be between" in e for e in errors)

    def test_is_valid_true(self):
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(api_config=api_config)
        assert config.is_valid() is True

    def test_is_valid_false(self):
        api_config = APIConfiguration()
        config = ApplicationConfiguration(api_config=api_config)
        assert config.is_valid() is False

    def test_tasks_property(self):
        api_config = APIConfiguration(openai_key='sk-test-key-1234567890')
        config = ApplicationConfiguration(api_config=api_config)
        assert config.tasks == TASKS
        assert len(config.tasks) == 3


class TestLoadConfig:
    """Test load_config and get_config functions."""

    def test_load_config_success(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-openai-key-1234567890'}):
            config = load_config()
            assert config.api_config.openai_key == 'sk-test-openai-key-1234567890'
            assert config.is_valid()

    def test_load_config_validation_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Configuration validation failed"):
                load_config()

    def test_get_config_not_loaded(self):
        import config.config_manager as cm
        old = cm._config
        cm._config = None
        try:
            with pytest.raises(RuntimeError, match="Configuration not loaded"):
                get_config()
        finally:
            cm._config = old

    def test_get_config_after_load(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-openai-key-1234567890'}):
            loaded = load_config()
            retrieved = get_config()
            assert retrieved is loaded
