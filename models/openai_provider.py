"""
OpenAI model provider - fetches and manages OpenAI models.
"""

from typing import List, Dict, Any, Callable

from openai import OpenAI

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error


class OpenAIModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "openai"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = OpenAI(api_key=api_key)
        temperature = self.default_temperature

        def call(prompt: str) -> str:
            completion = client.chat.completions.create(
                model=model_id,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content

        return call

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models

        try:
            client = OpenAI(api_key=self.api_key)
            models = client.models.list()

            model_ids = [m.id for m in models.data if is_text_model(m.id, 'openai')]
            chat_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]

            info(f"Fetched {len(chat_models)} OpenAI chat models dynamically")
            return chat_models

        except Exception as e:
            error(f"Failed to fetch OpenAI models: {e}")
            info("Falling back to predefined models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

        model_ids = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'openai')
        ]
