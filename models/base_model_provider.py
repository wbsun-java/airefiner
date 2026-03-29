"""
Base classes for model providers to eliminate code duplication.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

from config.constants import DEFAULT_TEMPERATURE
from utils.logger import LoggerMixin


class BaseModelProvider(ABC, LoggerMixin):
    """
    Base class for all model providers.
    """

    def __init__(self, api_key: str, provider_name: str):
        self.api_key = api_key
        self.provider_name = provider_name
        self.default_temperature = DEFAULT_TEMPERATURE

    @abstractmethod
    def fetch_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        """
        Return a callable that accepts a formatted prompt string and returns
        the model's text response.
        """
        pass

    def create_model_definition(self, model_id: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        if display_name is None:
            display_name = model_id
        return {
            "key": f"{self.provider_name}/{display_name}",
            "model_name": model_id,
            "provider": self,
        }
