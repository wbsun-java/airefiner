"""
Groq model provider - fetches and manages Groq models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info, error

try:
    from groq import Groq
except ImportError:
    Groq = None


class GroqModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "groq"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = Groq(api_key=api_key)
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
        try:
            if Groq is None:
                raise ImportError("groq package not available")

            client = Groq(api_key=self.api_key)
            models = client.models.list()

            model_ids = [m.id for m in models.data if is_text_model(m.id, 'groq')]
            groq_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]

            info(f"Fetched {len(groq_models)} Groq models dynamically")
            return groq_models

        except Exception as e:
            error(f"Failed to fetch Groq models: {e}")
            info("Falling back to predefined Groq models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        model_ids = [
            "llama-3.1-70b-versatile", "llama-3.1-8b-instant",
            "llama3-70b-8192", "llama3-8b-8192",
            "mixtral-8x7b-32768", "gemma2-9b-it",
        ]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'groq')
        ]
