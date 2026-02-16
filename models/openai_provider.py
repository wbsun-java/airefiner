"""
OpenAI model provider - fetches and manages OpenAI models.
"""

from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from openai import OpenAI

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error


class OpenAIModelProvider(BaseModelProvider):
    """
    OpenAI model provider using the official OpenAI SDK.
    """

    def __init__(self, api_key: str, provider_name: str = "openai"):
        super().__init__(api_key, provider_name)

    def get_model_class(self):
        return ChatOpenAI

    def get_model_id_key(self) -> str:
        return "model_name"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Dynamically fetch available OpenAI models from the API.
        Filters for chat completion models only.
        """
        from models.model_loader import is_text_model

        try:
            client = OpenAI(api_key=self.api_key)
            models = client.models.list()

            chat_models = []
            for model in models.data:
                model_id = model.id
                if is_text_model(model_id, 'openai'):
                    chat_models.append(self.create_model_definition(model_id))

            info(f"Fetched {len(chat_models)} OpenAI chat models dynamically")
            return chat_models

        except Exception as e:
            error(f"Failed to fetch OpenAI models: {e}")
            info("Falling back to predefined models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Fallback OpenAI models if dynamic fetching fails.
        """
        from models.model_loader import is_text_model

        model_ids = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'openai')
        ]
