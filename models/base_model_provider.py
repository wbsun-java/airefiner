"""
Base classes for model providers to eliminate code duplication.
"""

import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from config.constants import CacheConfig, InputConfig
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
        self.default_args = {"temperature": InputConfig.DEFAULT_TEMPERATURE}

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

    def initialize_models_with_fallback(self) -> List[Dict[str, Any]]:
        """
        Initialize models with fallback to predefined models if API call fails.
        
        Returns:
            List of model definitions
        """
        try:
            models = self.fetch_models()
            self.logger.info(f"✅ Fetched {len(models)} {self.provider_name} models dynamically")
            return models
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch {self.provider_name} models: {e}")
            self.logger.info(f"🔄 Falling back to predefined {self.provider_name} models")
            return self.get_fallback_models()

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

    def filter_models_by_keywords(self, models: List[Dict[str, Any]],
                                  include_keywords: List[str],
                                  exclude_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Filter models based on include/exclude keywords.
        
        Args:
            models: List of model dictionaries
            include_keywords: Keywords that must be present in model name
            exclude_keywords: Keywords that must not be present in model name
            
        Returns:
            Filtered list of models
        """
        if exclude_keywords is None:
            exclude_keywords = []

        filtered = []
        for model in models:
            model_name = model.get("model_name", "").lower()

            # Check include keywords
            has_include_keyword = any(keyword in model_name for keyword in include_keywords)
            if not has_include_keyword:
                continue

            # Check exclude keywords
            has_exclude_keyword = any(keyword in model_name for keyword in exclude_keywords)
            if has_exclude_keyword:
                continue

            filtered.append(model)

        return filtered


class CachedModelManager:
    """
    Manages caching of model definitions across providers.
    """

    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_timestamp = 0.0
        self.logger = LoggerMixin().logger

    def is_cache_valid(self) -> bool:
        """Check if the current cache is still valid."""
        current_time = time.time()
        return (self._cache and
                (current_time - self._cache_timestamp) < CacheConfig.DURATION_SECONDS)

    def get_cached_models(self) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Get cached model definitions if valid.
        
        Returns:
            Cached model definitions or None if cache is invalid
        """
        if self.is_cache_valid():
            self.logger.info("📋 Using cached model definitions")
            return self._cache.copy()
        return None

    def cache_models(self, model_definitions: Dict[str, List[Dict[str, Any]]]):
        """
        Cache model definitions.
        
        Args:
            model_definitions: Dictionary of provider -> models mapping
        """
        self._cache = model_definitions.copy()
        self._cache_timestamp = time.time()

        total_models = sum(len(models) for models in model_definitions.values())
        self.logger.info(f"💾 Model definitions cached for {CacheConfig.CACHE_DURATION_MINUTES} minutes")
        self.logger.info(f"📊 Total models after filtering: {total_models}")

    def clear_cache(self):
        """Clear the model cache."""
        self._cache.clear()
        self._cache_timestamp = 0.0
        self.logger.info("🗑️ Model cache cleared")


class ModelProviderFactory:
    """
    Factory class for creating model provider instances.
    """

    _provider_classes: Dict[str, type] = {}

    @classmethod
    def register_provider(cls, provider_name: str, provider_class: type):
        """
        Register a provider class.
        
        Args:
            provider_name: Name of the provider
            provider_class: Provider class that extends BaseModelProvider
        """
        cls._provider_classes[provider_name] = provider_class

    @classmethod
    def create_provider(cls, provider_name: str, api_key: str) -> Optional[BaseModelProvider]:
        """
        Create a provider instance.
        
        Args:
            provider_name: Name of the provider
            api_key: API key for the provider
            
        Returns:
            Provider instance or None if provider not registered
        """
        provider_class = cls._provider_classes.get(provider_name)
        if provider_class is None:
            return None
        return provider_class(api_key, provider_name)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of registered provider names."""
        return list(cls._provider_classes.keys())


class BaseModelInitializer(LoggerMixin):
    """
    Base class for model initialization with common error handling patterns.
    """

    def __init__(self, api_keys: Dict[str, str], api_key_arg_names: Dict[str, str]):
        """
        Initialize the model initializer.
        
        Args:
            api_keys: Dictionary mapping provider names to API keys
            api_key_arg_names: Dictionary mapping provider names to constructor argument names
        """
        self.api_keys = api_keys
        self.api_key_arg_names = api_key_arg_names
        self.initialized_models: Dict[str, Any] = {}
        self.initialization_errors: Dict[str, str] = {}

    def validate_provider_config(self, provider: str) -> bool:
        """
        Validate that a provider is properly configured.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider is configured, False otherwise
        """
        api_key_arg_name = self.api_key_arg_names.get(provider)
        if not api_key_arg_name:
            self.logger.warning(
                f"⚠️ Skipping provider '{provider}': Not configured in API_KEY_ARG_NAMES."
            )
            return False

        api_key = self.api_keys.get(provider)
        if not api_key:
            self.logger.warning(
                f"⚪ {provider.capitalize()} API Key not found, skipping {provider} models."
            )
            return False

        return True

    def initialize_model(self, model_def: Dict[str, Any], provider: str) -> bool:
        """
        Initialize a single model.
        
        Args:
            model_def: Model definition dictionary
            provider: Provider name
            
        Returns:
            True if initialization succeeded, False otherwise
        """
        model_key = model_def["key"]
        model_identifier_value = model_def["model_name"]
        model_class = model_def["class"]
        constructor_id_param_name = model_def.get("model_id_key")

        # Validate model definition
        if model_class is None:
            error_msg = f"Class definition missing for {model_key}."
            self.initialization_errors[model_key] = error_msg
            self.logger.warning(f"⚪ Skipping {model_key}: {error_msg}")
            return False

        if not constructor_id_param_name:
            error_msg = f"Configuration error: 'model_id_key' missing for {model_key}."
            self.initialization_errors[model_key] = error_msg
            self.logger.warning(f"⚪ Skipping {model_key}: {error_msg}")
            return False

        # Build constructor arguments
        model_args_from_def = model_def["args"].copy()
        api_key_arg_name = self.api_key_arg_names[provider]
        model_args_from_def[api_key_arg_name] = self.api_keys[provider]

        try:
            constructor_kwargs = {constructor_id_param_name: model_identifier_value}
            final_constructor_args = {**constructor_kwargs, **model_args_from_def}

            self.initialized_models[model_key] = model_class(**final_constructor_args)
            self.logger.info(f"✅ Initialized {model_key}")
            return True

        except Exception as e:
            error_msg = f"Failed to initialize {model_key}: {e}"
            self.initialization_errors[model_key] = error_msg
            self.logger.error(f"❌ {error_msg}")
            return False

    def get_results(self) -> tuple[Dict[str, Any], Dict[str, str]]:
        """
        Get initialization results.
        
        Returns:
            Tuple of (initialized_models, initialization_errors)
        """
        return self.initialized_models, self.initialization_errors
