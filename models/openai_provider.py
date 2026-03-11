"""
OpenAI model provider - fetches and manages OpenAI models.
"""

import re
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from openai import OpenAI

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error

# Matches YYYY-MM-DD or 4-digit MMDD date suffixes, optionally followed by a word like -preview
# e.g. gpt-4o-2024-11-20, gpt-3.5-turbo-1106, gpt-4-0125-preview
_DATE_SUFFIX = re.compile(r'-(\d{4}-\d{2}-\d{2}|\d{4})(?:-[a-z]+)?$')


def _deduplicate_models(model_ids: List[str]) -> List[str]:
    """
    Keep base/undated models only. Dated snapshots are dropped when a base exists.
    If no base exists for a dated model, keep the latest snapshot as fallback.
    e.g. gpt-4o, gpt-4o-2024-05-13, gpt-4o-2024-08-06, gpt-4o-2024-11-20 -> gpt-4o
    """
    model_set = set(model_ids)
    dated: Dict[str, list] = {}  # base -> [(model_id, date_str)]
    undated: List[str] = []

    for model_id in model_ids:
        m = _DATE_SUFFIX.search(model_id)
        if m:
            base = model_id[:m.start()]
            dated.setdefault(base, []).append((model_id, m.group(1)))
        else:
            undated.append(model_id)

    result = list(undated)
    for base, versions in dated.items():
        if base not in model_set:
            # No base model exists — keep latest dated version as fallback
            result.append(max(versions, key=lambda x: x[1])[0])

    return sorted(result)


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
        from models.model_filter import is_text_model

        try:
            client = OpenAI(api_key=self.api_key)
            models = client.models.list()

            model_ids = [m.id for m in models.data if is_text_model(m.id, 'openai')]
            chat_models = [self.create_model_definition(m) for m in _deduplicate_models(model_ids)]

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
        from models.model_filter import is_text_model

        model_ids = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'openai')
        ]
