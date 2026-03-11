"""
Base classes for model providers to eliminate code duplication.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from config.constants import DEFAULT_TEMPERATURE
from utils.logger import LoggerMixin


class BaseModelProvider(ABC, LoggerMixin):
    """
    Base class for all model providers.
    Provides common functionality for fetching models and handling fallbacks.
    """

    def __init__(self, api_key: str, provider_name: str):
        """
        Initialize the base model provider.
        
        Args:
            api_key: API key for the provider
            provider_name: Name of the provider (e.g., 'openai', 'anthropic')
        """
        self.api_key = api_key
        self.provider_name = provider_name
        self.default_args = {"temperature": DEFAULT_TEMPERATURE}

    @abstractmethod
    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available models from the provider's API.
        
        Returns:
            List of model dictionaries with standardized format
        """
        pass

    @abstractmethod
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Get fallback models when API fetching fails.
        
        Returns:
            List of predefined model dictionaries
        """
        pass

    @abstractmethod
    def get_model_class(self):
        """
        Get the LangChain model class for this provider.
        
        Returns:
            The LangChain chat model class
        """
        pass

    @abstractmethod
    def get_model_id_key(self) -> str:
        """
        Get the parameter name used for model ID in the constructor.
        
        Returns:
            Parameter name (e.g., 'model_name', 'model')
        """
        pass

    def create_model_definition(self, model_id: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a standardized model definition dictionary.
        
        Args:
            model_id: The model identifier used by the API
            display_name: Optional display name (defaults to model_id)
            
        Returns:
            Standardized model definition dictionary
        """
        if display_name is None:
            display_name = model_id

        return {
            "key": f"{self.provider_name}/{display_name}",
            "model_name": model_id,
            "class": self.get_model_class(),
            "args": self.default_args.copy(),
            "model_id_key": self.get_model_id_key()
        }

