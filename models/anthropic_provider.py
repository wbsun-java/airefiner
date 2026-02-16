"""
Anthropic model provider - fetches and manages Anthropic Claude models.
"""

from typing import List, Dict, Any

from langchain_anthropic import ChatAnthropic

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error

try:
    import anthropic as anthropic_sdk
except ImportError:
    anthropic_sdk = None


class AnthropicModelProvider(BaseModelProvider):
    """
    Anthropic model provider using the official Anthropic SDK.
    """

    def __init__(self, api_key: str, provider_name: str = "anthropic"):
        super().__init__(api_key, provider_name)

    def get_model_class(self):
        return ChatAnthropic

    def get_model_id_key(self) -> str:
        return "model"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Dynamically fetch available Anthropic Claude models from the API.
        """
        from models.model_loader import is_text_model

        try:
            if anthropic_sdk is None:
                raise ImportError("anthropic package not available")

            client = anthropic_sdk.Anthropic(api_key=self.api_key)
            models_page = client.models.list()

            anthropic_models = []
            for model in models_page.data:
                model_id = model.id
                display_name = getattr(model, 'display_name', model_id) or model_id

                if model_id and is_text_model(model_id, 'anthropic') and "claude" in model_id.lower():
                    anthropic_models.append(self.create_model_definition(model_id, display_name))

            info(f"Fetched {len(anthropic_models)} Anthropic Claude models dynamically")
            return anthropic_models

        except Exception as e:
            error(f"Failed to fetch Anthropic models: {e}")
            info("Falling back to predefined Claude models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Fallback Anthropic models if dynamic fetching fails.
        """
        from models.model_loader import is_text_model

        fallback_models = [
            ("claude-3-5-sonnet-20241022", "Claude Sonnet 3.5"),
            ("claude-3-7-sonnet-20250219", "Claude Sonnet 3.7"),
            ("claude-sonnet-4-20250514", "Claude Sonnet 4"),
            ("claude-opus-4-20250514", "Claude Opus 4"),
            ("claude-3-5-haiku-20241022", "Claude Haiku 3.5"),
        ]
        return [
            self.create_model_definition(model_id, display_name)
            for model_id, display_name in fallback_models
            if is_text_model(model_id, 'anthropic')
        ]
