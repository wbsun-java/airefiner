"""
Base classes for model providers to eliminate code duplication.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

from config.constants import DEFAULT_TEMPERATURE
from models.model_filter import is_text_model
from utils.logger import info, error, LoggerMixin


class BaseModelProvider(ABC, LoggerMixin):
    """
    Base class for all model providers.
    """

    def __init__(self, api_key: str, provider_name: str):
        self.api_key = api_key
        self.provider_name = provider_name
        self.default_temperature = DEFAULT_TEMPERATURE

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch models, falling back to get_fallback_models() on any error."""
        try:
            return self._do_fetch_models()
        except Exception as e:
            error(f"Failed to fetch {self.provider_name} models: {e}")
            info(f"Falling back to predefined {self.provider_name} models")
            return self.get_fallback_models()

    @abstractmethod
    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        pass

    def _build_fallback_list(self, model_ids: List[str]) -> List[Dict[str, Any]]:
        """Build model definitions from a list of IDs, filtering non-text models."""
        return [
            self.create_model_definition(m)
            for m in model_ids
            if is_text_model(m, self.provider_name)
        ]

    def create_model_definition(
        self, model_id: str, display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        if display_name is None:
            display_name = model_id
        return {
            "key": f"{self.provider_name}/{display_name}",
            "model_name": model_id,
            "provider": self,
        }
