"""
Model loader - orchestrates dynamic fetching and initialization of AI models from multiple providers.
"""

import time
from typing import Dict, Any, Tuple

from config.config_manager import get_config
from config.constants import CacheConfig, ModelFiltering
from utils.logger import info, warning, error

# Global cache for model definitions
_model_cache = {}
_cache_timestamp = 0

# Provider registry: maps provider name to its provider class import path.
# Each entry is (module_path, class_name).
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


def is_text_model(model_id: str, provider: str = "") -> bool:
    """
    Filter to identify text-based models suitable for content refinement.
    Uses keyword heuristics to exclude image/audio/video/embedding models.
    Can be disabled or customized via config_manager.py configuration.
    """
    config = get_config()
    if not config.model_filtering.enable_strict_filtering:
        return True

    model_id_lower = model_id.lower()

    non_text_keywords = ModelFiltering.NON_TEXT_KEYWORDS.copy()
    non_text_keywords.extend([kw.lower() for kw in config.model_filtering.custom_exclude_keywords])
    non_text_keywords.extend(['image', 'video', 'audio', 'robot', 'embed', 'dall-e', 'tts', 'whisper', 'vision-only'])

    for keyword in non_text_keywords:
        if keyword in model_id_lower:
            info(f"🔎 Filtering out non-text model ({keyword}): {model_id}")
            return False

    provider_exclusions = ModelFiltering.PROVIDER_EXCLUSIONS
    if provider and provider in provider_exclusions:
        for excluded in provider_exclusions[provider]:
            if excluded.lower() in model_id_lower:
                info(f"🔎 Filtering out provider-specific non-text model: {model_id}")
                return False

    if not any(ind in model_id_lower for ind in ModelFiltering.TEXT_INDICATORS):
        info(f"🔎 Model may not be text-focused (no text indicators): {model_id}")
        return False

    return True


def get_model_definitions() -> Dict[str, list]:
    """
    Fetch model definitions from all providers with 1-hour caching.
    Falls back to predefined models when API calls fail.
    """
    global _model_cache, _cache_timestamp

    current_time = time.time()
    if _model_cache and (current_time - _cache_timestamp) < CacheConfig.DURATION_SECONDS:
        info("📋 Using cached model definitions")
        return _model_cache

    config = get_config()
    api_keys = config.api_config.get_api_keys()

    model_definitions = {}
    for provider_name in _PROVIDER_REGISTRY:
        api_key = api_keys.get(provider_name)
        try:
            provider_cls = _get_provider_class(provider_name)
            provider = provider_cls(api_key=api_key or "")
            if api_key:
                model_definitions[provider_name] = provider.fetch_models()
            else:
                warning(f"⚪ {provider_name.capitalize()} API key not found, using fallback models")
                model_definitions[provider_name] = provider.get_fallback_models()
        except Exception as e:
            error(f"❌ Failed to load {provider_name} provider: {e}")
            model_definitions[provider_name] = []

    _model_cache = model_definitions
    _cache_timestamp = current_time
    info(f"💾 Model definitions cached for {CacheConfig.CACHE_DURATION_MINUTES} minutes")
    info(f"📊 Total models after filtering: {sum(len(m) for m in model_definitions.values())}")

    return model_definitions


def initialize_models() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Initialize all AI models from model definitions using appropriate LangChain classes.
    Returns (initialized_models, initialization_errors).
    """
    initialized_models = {}
    initialization_errors = {}

    info("\n--- Initializing Models (from models/model_loader.py) ---")

    config = get_config()
    api_keys = config.api_config.get_api_keys()
    api_key_arg_names = config.api_config.api_key_arg_names

    try:
        from models.xai_provider import ChatXAIGRPC as ChatXAI
    except ImportError:
        ChatXAI = None

    for provider, model_list in get_model_definitions().items():
        api_key = api_keys.get(provider)
        api_key_arg_name = api_key_arg_names.get(provider)

        if not api_key_arg_name:
            warning(f"\n⚠️ Skipping provider '{provider}': Not configured in api_key_arg_names.")
            for md in model_list:
                initialization_errors[md["key"]] = f"Provider '{provider}' not configured."
            continue

        if provider == "xai" and ChatXAI is None:
            warning(f"\n⚪ Skipping xAI models: ChatXAIGRPC not available. Install xai-sdk.")
            for md in model_list:
                initialization_errors[md["key"]] = "ChatXAIGRPC not available."
            continue

        if not api_key:
            warning(f"\n⚪ {provider.capitalize()} API Key not found, skipping {provider} models.")
            for md in model_list:
                initialization_errors[md["key"]] = f"{provider.capitalize()} API Key not found."
            continue

        info(f"\n-- Initializing {provider.capitalize()} models --")
        for md in model_list:
            model_key = md["key"]
            model_class = md["class"]
            model_id_key = md.get("model_id_key")

            if model_class is None or not model_id_key:
                err = f"Invalid model definition for {model_key}."
                initialization_errors[model_key] = err
                warning(f"⚪ Skipping {model_key}: {err}")
                continue

            try:
                args = md["args"].copy()
                args[api_key_arg_name] = api_key
                args[model_id_key] = md["model_name"]
                initialized_models[model_key] = model_class(**args)
                info(f"✅ Initialized {model_key}")
            except Exception as e:
                err = f"Failed to initialize {model_key}: {e}"
                initialization_errors[model_key] = err
                error(f"❌ {err}")

    info("\n--- Model Initialization Complete ---")
    if initialization_errors:
        warning("Some models failed to initialize. They will not be available for selection.")

    return initialized_models, initialization_errors
