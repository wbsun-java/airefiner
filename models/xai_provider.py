"""
xAI model provider - fetches and manages xAI Grok models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error


class XAIModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "xai"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        from xai_sdk import Client
        from xai_sdk.chat import user as xai_user

        client = Client(api_key=api_key)

        def call(prompt: str) -> str:
            chat = client.chat.create(model=model_id)
            chat.append(xai_user(prompt))
            response = chat.sample()
            return response.content

        return call

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models
        from xai_sdk import Client

        try:
            client = Client(api_key=self.api_key)
            language_models = client.models.list_language_models()
            model_ids = [
                m.name for m in language_models
                if is_text_model(m.name, 'xai')
            ]
            models = [
                self.create_model_definition(m)
                for m in deduplicate_models(model_ids)
            ]
            info(f"Fetched {len(models)} xAI models dynamically")
            return models
        except Exception as e:
            error(f"Failed to fetch xAI models: {e}")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

        model_ids = ["grok-4-0709", "grok-3", "grok-3-mini"]
        return [self.create_model_definition(m) for m in model_ids
                if is_text_model(m, 'xai')]
