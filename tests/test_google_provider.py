"""Unit tests for Google Gemini model discovery."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from models.google_provider import GoogleModelProvider


class TestGoogleModelDiscovery:
    def test_filters_retired_models_returned_by_google(self):
        models = [
            SimpleNamespace(
                name="models/gemini-2.0-flash",
                supported_actions=["generateContent"],
            ),
            SimpleNamespace(
                name="models/gemini-2.5-flash",
                supported_actions=["generateContent"],
            ),
            SimpleNamespace(
                name="models/gemini-3.5-flash",
                supported_actions=["generateContent"],
            ),
        ]
        client = Mock()
        client.models.list.return_value = models

        fake_genai = SimpleNamespace(Client=Mock(return_value=client))
        with patch("models.google_provider.genai", fake_genai):
            result = GoogleModelProvider("test-key")._do_fetch_models()

        assert [model["model_name"] for model in result] == [
            "gemini-2.5-flash",
            "gemini-3.5-flash",
        ]

    def test_fallback_models_exclude_retired_generations(self):
        result = GoogleModelProvider("test-key").get_fallback_models()
        model_ids = [model["model_name"] for model in result]

        assert "gemini-3.5-flash" in model_ids
        assert not any(model_id.startswith("gemini-2.0-") for model_id in model_ids)
        assert not any(model_id.startswith("gemini-1.5-") for model_id in model_ids)
