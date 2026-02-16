"""
Google Gemini model provider - fetches and manages Google AI models.
"""

import time
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI

from models.base_model_provider import BaseModelProvider
from utils.logger import info, warning, error

try:
    from google import genai
except ImportError:
    genai = None


class GoogleModelProvider(BaseModelProvider):
    """
    Google model provider using the google-genai SDK.
    """

    def __init__(self, api_key: str, provider_name: str = "google"):
        super().__init__(api_key, provider_name)

    def get_model_class(self):
        return ChatGoogleGenerativeAI

    def get_model_id_key(self) -> str:
        return "model"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Dynamically fetch available Google Gemini models from the API.
        """
        from models.model_loader import is_text_model

        try:
            if genai is None:
                raise ImportError("google-genai package not available")

            client = genai.Client(api_key=self.api_key)

            max_retries = 3
            models = []
            for attempt in range(max_retries):
                try:
                    models = list(client.models.list())
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        warning(f"Attempt {attempt + 1} failed to fetch Google models: {e}. Retrying...")
                        time.sleep(2)
                    else:
                        raise e

            google_models = []
            for model in models:
                model_name = model.name.split('/')[-1] if '/' in model.name else model.name
                supported_actions = getattr(model, 'supported_actions', None)
                if supported_actions:
                    supported_actions = [action for action in supported_actions]

                if (is_text_model(model_name, 'google') and "gemini" in model_name.lower() and
                        (supported_actions is None or 'generateContent' in supported_actions)):
                    google_models.append(self.create_model_definition(model_name))

            info(f"Fetched {len(google_models)} Google Gemini models dynamically")
            return google_models

        except Exception as e:
            error(f"Failed to fetch Google models: {e}")
            info("Falling back to predefined Gemini models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Fallback Google models if dynamic fetching fails.
        """
        from models.model_loader import is_text_model

        model_ids = [
            "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp",
            "gemini-2.5-flash", "gemini-2.5-pro",
        ]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'google')
        ]
