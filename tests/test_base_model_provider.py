"""
Unit tests for BaseModelProvider shared helpers.
"""
from unittest.mock import patch, Mock
import pytest
from models.base_model_provider import BaseModelProvider


class ConcreteProvider(BaseModelProvider):
    """Minimal concrete provider for testing the base class."""

    def _do_fetch_models(self):
        return [{"key": "p/m", "model_name": "m", "provider": self}]

    def get_fallback_models(self):
        return [{"key": "p/fallback", "model_name": "fallback", "provider": self}]

    def build_callable(self, model_id, api_key):
        return lambda prompt: "response"


@pytest.fixture
def provider():
    return ConcreteProvider(api_key="test-key", provider_name="testprovider")


class TestFetchModelsTemplate:
    def test_returns_do_fetch_result_on_success(self, provider):
        result = provider.fetch_models()
        assert result == [{"key": "p/m", "model_name": "m", "provider": provider}]

    def test_falls_back_on_exception(self, provider):
        with patch.object(provider, '_do_fetch_models', side_effect=RuntimeError("API down")):
            result = provider.fetch_models()
        assert result == [{"key": "p/fallback", "model_name": "fallback", "provider": provider}]

    def test_logs_error_on_exception(self, provider):
        with patch('models.base_model_provider.error') as mock_error, \
             patch.object(provider, '_do_fetch_models', side_effect=RuntimeError("API down")):
            provider.fetch_models()
        mock_error.assert_called_once()
        assert "testprovider" in mock_error.call_args[0][0]


class TestBuildFallbackList:
    def test_returns_definitions_for_valid_ids(self, provider):
        with patch('models.base_model_provider.is_text_model', return_value=True):
            result = provider._build_fallback_list(["model-a", "model-b"])
        assert len(result) == 2
        assert result[0]["model_name"] == "model-a"
        assert result[1]["model_name"] == "model-b"

    def test_filters_non_text_models(self, provider):
        def fake_is_text(model_id, provider_name):
            return model_id != "model-b"

        with patch('models.base_model_provider.is_text_model', side_effect=fake_is_text):
            result = provider._build_fallback_list(["model-a", "model-b"])
        assert len(result) == 1
        assert result[0]["model_name"] == "model-a"

    def test_uses_provider_name_for_filtering(self, provider):
        captured = []

        def capture_call(model_id, provider_name):
            captured.append(provider_name)
            return True

        with patch('models.base_model_provider.is_text_model', side_effect=capture_call):
            provider._build_fallback_list(["m"])
        assert captured == ["testprovider"]
