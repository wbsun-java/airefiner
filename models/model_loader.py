"""
Model loader - orchestrates dynamic fetching and initialization of AI models from multiple providers.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Tuple

from config.config_manager import get_config
from config.constants import CACHE_DURATION_SECONDS
from utils.logger import info, warning, error

_model_cache = {}
_cache_timestamp = 0

_PROVIDER_REGISTRY = {
    "openai": ("models.openai_provider", "OpenAIModelProvider"),
    "google": ("models.google_provider", "GoogleModelProvider"),
    "anthropic": ("models.anthropic_provider", "AnthropicModelProvider"),
    "groq": ("models.groq_provider", "GroqModelProvider"),
    "xai": ("models.xai_provider", "XAIModelProvider"),
}


def _get_provider_class(provider_name: str):
    """Lazily import and return a provider class by name."""
    import importlib
    module_path, class_name = _PROVIDER_REGISTRY[provider_name]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_model_definitions() -> Dict[str, list]:
    """
    Fetch model definitions from all providers with 1-hour caching.
    Falls back to predefined models when API calls fail.
    """
    global _model_cache, _cache_timestamp

    current_time = time.time()
    if _model_cache and (current_time - _cache_timestamp) < CACHE_DURATION_SECONDS:
        info("📋 Using cached model definitions")
        return _model_cache

    config = get_config()
    api_keys = config.api_config.get_api_keys()

    def _load_provider(provider_name: str) -> tuple[str, list]:
        api_key = api_keys.get(provider_name)
        try:
            provider_cls = _get_provider_class(provider_name)
            provider = provider_cls(api_key=api_key or "")
            if api_key:
                return provider_name, provider.fetch_models()
            else:
                warning(f"⚪ {provider_name.capitalize()} API key not found, using fallback models")
                return provider_name, provider.get_fallback_models()
        except Exception as e:
            error(f"❌ Failed to load {provider_name} provider: {e}")
            return provider_name, []

    model_definitions = {}
    with ThreadPoolExecutor(max_workers=len(_PROVIDER_REGISTRY)) as executor:
        futures = {executor.submit(_load_provider, name): name for name in _PROVIDER_REGISTRY}
        for future in as_completed(futures):
            provider_name, models = future.result()
            model_definitions[provider_name] = models

    _model_cache = model_definitions
    _cache_timestamp = current_time
    info(f"💾 Model definitions cached for {CACHE_DURATION_SECONDS // 60} minutes")
    info(f"📊 Total models after filtering: {sum(len(m) for m in model_definitions.values())}")

    return model_definitions


def initialize_models() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Initialize all AI models from model definitions.
    Returns (initialized_models, initialization_errors).
    """
    initialized_models = {}
    initialization_errors = {}

    info("\n--- Initializing Models (from models/model_loader.py) ---")

    config = get_config()
    api_keys = config.api_config.get_api_keys()

    for provider_name, model_list in get_model_definitions().items():
        api_key = api_keys.get(provider_name)

        if not api_key:
            warning(f"\n⚪ {provider_name.capitalize()} API Key not found, skipping {provider_name} models.")
            for md in model_list:
                initialization_errors[md["key"]] = f"{provider_name.capitalize()} API Key not found."
            continue

        info(f"\n-- Initializing {provider_name.capitalize()} models --")
        for md in model_list:
            model_key = md["key"]
            provider = md["provider"]

            try:
                initialized_models[model_key] = provider.build_callable(md["model_name"], api_key)
                info(f"✅ Initialized {model_key}")
            except Exception as e:
                err = f"Failed to initialize {model_key}: {e}"
                initialization_errors[model_key] = err
                error(f"❌ {err}")

    info("\n--- Model Initialization Complete ---")
    if initialization_errors:
        warning("Some models failed to initialize. They will not be available for selection.")

    return initialized_models, initialization_errors
