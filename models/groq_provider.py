"""
Groq model provider - fetches and manages Groq models.
"""

from typing import List, Dict, Any

from langchain_groq import ChatGroq

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error

try:
    from groq import Groq
except ImportError:
    Groq = None


class GroqModelProvider(BaseModelProvider):
    """
    Groq model provider using the official Groq SDK.
    """

    def __init__(self, api_key: str, provider_name: str = "groq"):
        super().__init__(api_key, provider_name)

    def get_model_class(self):
        return ChatGroq

    def get_model_id_key(self) -> str:
        return "model_name"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Dynamically fetch available Groq models from the API.
        """
        from models.model_loader import is_text_model

        try:
            if Groq is None:
                raise ImportError("groq package not available")

            client = Groq(api_key=self.api_key)
            models = client.models.list()

            groq_models = []
            for model in models.data:
                model_id = model.id
                if is_text_model(model_id, 'groq'):
                    groq_models.append(self.create_model_definition(model_id))

            info(f"Fetched {len(groq_models)} Groq models dynamically")
            return groq_models

        except Exception as e:
            error(f"Failed to fetch Groq models: {e}")
            info("Falling back to predefined Groq models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Fallback Groq models if dynamic fetching fails.
        """
        from models.model_loader import is_text_model

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
