"""
Google Gemini model provider - fetches and manages Google AI models.
"""

import time
from typing import List, Dict, Any, Callable

try:
    from google import genai
except ImportError:  # pragma: no cover - depends on the local optional dependency
    genai = None

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info, warning


# Google can continue returning shut-down model IDs from models.list(). Keep
# lifecycle filtering separate from capability filtering so retired text models
# are not presented as usable choices.
_RETIRED_MODEL_PREFIXES = (
    "gemini-1.0-",
    "gemini-1.5-",
    "gemini-2.0-",
)


def _is_available_model(model_id: str) -> bool:
    """Return whether a Gemini model family is still callable."""
    return not model_id.lower().startswith(_RETIRED_MODEL_PREFIXES)


class GoogleModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "google"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        if genai is None:
            raise ImportError("google-genai package is not available")
        client = genai.Client(api_key=api_key)
        temperature = self.default_temperature

        def call(prompt: str) -> str:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=genai.types.GenerateContentConfig(temperature=temperature),
            )
            return response.text

        return call

    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        if genai is None:
            raise ImportError("google-genai package is not available")
        client = genai.Client(api_key=self.api_key)

        max_retries = 3
        models = []
        for attempt in range(max_retries):
            try:
                models = list(client.models.list())
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                warning(
                    f"Attempt {attempt + 1} failed to fetch Google models: {e}. Retrying..."
                )
                time.sleep(2)

        model_ids = []
        for model in models:
            model_name = model.name.split('/')[-1] if '/' in model.name else model.name
            supported_actions = getattr(model, 'supported_actions', None)
            if (_is_available_model(model_name) and
                    is_text_model(model_name, 'google') and "gemini" in model_name.lower() and
                    (supported_actions is None or 'generateContent' in supported_actions)):
                model_ids.append(model_name)

        google_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]
        info(f"Fetched {len(google_models)} Google Gemini models dynamically")
        return google_models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        return self._build_fallback_list([
            "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview",
            "gemini-2.5-flash", "gemini-2.5-pro",
        ])
