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
<<<<<<< HEAD
    Comprehensive filtering to identify text-based models suitable for content refinement.
    
    This function uses heuristics and keyword matching to determine if a model is appropriate
    for text processing tasks like content refinement and translation. It excludes models
    designed for image generation, audio processing, embeddings, and other non-text tasks.
    
    The filtering can be disabled or customized via settings.py configuration.
    
    Args:
        model_id: The model identifier to evaluate (e.g., "gpt-4o", "dall-e-3")
        provider: Optional provider name for provider-specific filtering rules
        
    Returns:
        bool: True if the model appears to be suitable for text processing, False otherwise
        
    Example:
        >>> is_text_model("gpt-4o", "openai")
        True
        >>> is_text_model("dall-e-3", "openai")  
        False
        >>> is_text_model("whisper-1", "openai")
        False
    """
    # Skip filtering if disabled in settings
    if not ENABLE_STRICT_MODEL_FILTERING:
        return True

    model_id_lower = model_id.lower()

    # Common non-text keywords from configuration
    non_text_keywords = ModelFiltering.NON_TEXT_KEYWORDS.copy()

    # Ensure mandatory non-text keywords are included (image, robot, etc.)
    mandatory_exclusions = ["image", "robot", "audio", "video", "embedding", "moderation"]
    for kw in mandatory_exclusions:
        if kw not in non_text_keywords:
            non_text_keywords.append(kw)

    # Add custom exclude keywords from settings
    non_text_keywords.extend([keyword.lower() for keyword in CUSTOM_EXCLUDE_KEYWORDS])

    # Provider-specific exclusions from configuration
    provider_specific_exclusions = ModelFiltering.PROVIDER_EXCLUSIONS

    # Check common non-text keywords
    for keyword in non_text_keywords:
        if keyword in model_id_lower:
            info(f"🔎 Filtering out non-text model ({keyword}): {model_id}")
            return False

    # Check provider-specific exclusions
    if provider and provider in provider_specific_exclusions:
        for excluded_model in provider_specific_exclusions[provider]:
            if excluded_model.lower() in model_id_lower:
                info(f"🔎 Filtering out provider-specific non-text model: {model_id}")
                return False

    # Additional heuristics for text model identification
    # Models with these patterns are likely text models
    text_indicators = ModelFiltering.TEXT_INDICATORS

    has_text_indicator = any(indicator in model_id_lower for indicator in text_indicators)

    if not has_text_indicator:
        info(f"🔎 Model may not be text-focused (no text indicators): {model_id}")
        return False

    return True


# --- Dynamic Model Fetching Functions ---
def fetch_openai_models(api_key: str) -> List[Dict[str, Any]]:
    """
    Dynamically fetch available OpenAI models from the API.
    Filters for chat completion models only.
    """
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()

        chat_models = []
        for model in models.data:
            model_id = model.id
            # Filter for GPT models that support chat completions AND are text-based
            if is_text_model(model_id, 'openai') and any(
                    prefix in model_id.lower() for prefix in ['gpt-4', 'gpt-3.5', 'o1']):
                chat_models.append({
                    "key": f"openai/{model_id}",
                    "model_name": model_id,
                    "class": ChatOpenAI,
                    "args": {"temperature": 0.7},
                    "model_id_key": "model_name"
                })

        info(f"✅ Fetched {len(chat_models)} OpenAI chat models dynamically")
        return chat_models

    except Exception as e:
        error(f"❌ Failed to fetch OpenAI models: {e}")
        info("🔄 Falling back to predefined models")
        return get_fallback_openai_models()


def get_fallback_openai_models() -> List[Dict[str, Any]]:
    """
    Fallback OpenAI models if dynamic fetching fails.
    """
    all_models = [
        {"key": "openai/gpt-4o", "model_name": "gpt-4o", "class": ChatOpenAI, 
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "openai/gpt-4o-mini", "model_name": "gpt-4o-mini", "class": ChatOpenAI,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "openai/gpt-4-turbo", "model_name": "gpt-4-turbo", "class": ChatOpenAI,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "openai/gpt-3.5-turbo", "model_name": "gpt-3.5-turbo", "class": ChatOpenAI,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
    ]
    return [model for model in all_models if is_text_model(model["model_name"], 'openai')]


def fetch_xai_models(api_key: str) -> List[Dict[str, Any]]:
    """
    Dynamically fetch available xAI models from the API.
    xAI API is OpenAI-compatible, so we use OpenAI client with custom base_url.
    """
    try:
        # Use OpenAI client with xAI endpoint since they're API-compatible
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        models = client.models.list()

        grok_models = []
        for model in models.data:
            model_id = model.id
            # Filter for Grok models that are text-based
            if is_text_model(model_id, 'xai') and any(prefix in model_id.lower() for prefix in ['grok']):
                grok_models.append({
                    "key": f"xAI/{model_id}",
                    "model_name": model_id,
                    "class": ChatXAI,
                    "args": {"temperature": 0.7},
                    "model_id_key": "model"
                })

        info(f"✅ Fetched {len(grok_models)} xAI Grok models dynamically")
        return grok_models

    except Exception as e:
        error(f"❌ Failed to fetch xAI models: {e}")
        info("🔄 Falling back to predefined Grok models")
        return get_fallback_xai_models()


def get_fallback_xai_models() -> List[Dict[str, Any]]:
    """
    Fallback xAI models if dynamic fetching fails.
    """
    all_models = [
        {"key": "xAI/grok-beta", "model_name": "grok-beta", "class": ChatXAI,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "xAI/grok-2", "model_name": "grok-2", "class": ChatXAI,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "xAI/grok-2-mini", "model_name": "grok-2-mini", "class": ChatXAI,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "xAI/grok-3", "model_name": "grok-3", "class": ChatXAI,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
    ]
    return [model for model in all_models if is_text_model(model["model_name"], 'xai')]


def fetch_google_models(api_key: str) -> List[Dict[str, Any]]:
    """
    Dynamically fetch available Google Gemini models from the API.
    """
    try:
        if genai is None:
            raise ImportError("google-generativeai package not available")

        genai.configure(api_key=api_key)

        models = genai.list_models()

        google_models = []
        for model in models:
            model_name = model.name.split('/')[-1] if '/' in model.name else model.name

            if is_text_model(model_name, 'google') and hasattr(model, 'supported_generation_methods'):
                supported_methods = [method for method in model.supported_generation_methods]
                if 'generateContent' in supported_methods:
                    google_models.append({
                        "key": f"google/{model_name}",
                        "model_name": model_name,
                        "class": ChatGoogleGenerativeAI,
                        "args": {"temperature": 0.7},
                        "model_id_key": "model"
                    })

        info(f"✅ Fetched {len(google_models)} Google Gemini models dynamically")
        return google_models

    except Exception as e:
        error(f"❌ Failed to fetch Google models: {e}")
        info("🔄 Falling back to predefined Gemini models")
        return get_fallback_google_models()


def get_fallback_google_models() -> List[Dict[str, Any]]:
    """
    Fallback Google models if dynamic fetching fails.
    """
    all_models = [
        {"key": "google/gemini-1.5-flash", "model_name": "gemini-1.5-flash",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemini-1.5-pro", "model_name": "gemini-1.5-pro",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemini-2.0-flash-exp", "model_name": "gemini-2.0-flash-exp",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemini-2.5-flash", "model_name": "gemini-2.5-flash",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemini-2.5-pro", "model_name": "gemini-2.5-pro",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
    ]
    return [model for model in all_models if is_text_model(model["model_name"], 'google')]


def fetch_anthropic_models(api_key: str) -> List[Dict[str, Any]]:
    """
    Dynamically fetch available Anthropic Claude models from the API.
    """
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        anthropic_models = []
        for model in data.get("data", []):
            model_id = model.get("id")
            display_name = model.get("display_name", model_id)

            if model_id and is_text_model(model_id, 'anthropic') and "claude" in model_id.lower():
                anthropic_models.append({
                    "key": f"anthropic/{display_name}",
                    "model_name": model_id,
                    "class": ChatAnthropic,
                    "args": {"temperature": 0.7},
                    "model_id_key": "model_name"
                })

        info(f"✅ Fetched {len(anthropic_models)} Anthropic Claude models dynamically")
        return anthropic_models

    except Exception as e:
        error(f"❌ Failed to fetch Anthropic models: {e}")
        info("🔄 Falling back to predefined Claude models")
        return get_fallback_anthropic_models()


def get_fallback_anthropic_models() -> List[Dict[str, Any]]:
    """
    Fallback Anthropic models if dynamic fetching fails.
    """
    all_models = [
        {"key": "anthropic/Claude Sonnet 3.5", "model_name": "claude-3-5-sonnet-20241022",
         "class": ChatAnthropic, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/Claude Sonnet 3.7", "model_name": "claude-3-7-sonnet-20250219",
         "class": ChatAnthropic, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/Claude Sonnet 4", "model_name": "claude-sonnet-4-20250514",
         "class": ChatAnthropic, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/Claude Opus 4", "model_name": "claude-opus-4-20250514",
         "class": ChatAnthropic, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/Claude Haiku 3.5", "model_name": "claude-3-5-haiku-20241022",
         "class": ChatAnthropic, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
    ]
    return [model for model in all_models if is_text_model(model["model_name"], 'anthropic')]


def fetch_groq_models(api_key: str) -> List[Dict[str, Any]]:
    """
    Dynamically fetch available Groq models from the API.
    """
    try:
        if Groq is None:
            raise ImportError("groq package not available")

        client = Groq(api_key=api_key)

        models = client.models.list()

        groq_models = []
        for model in models.data:
            model_id = model.id

            if is_text_model(model_id, 'groq') and any(
                    prefix in model_id.lower() for prefix in ['llama', 'gemma', 'qwen', 'deepseek', 'mistral']):
                if 'guard' not in model_id.lower():
                    groq_models.append({
                        "key": f"groq/{model_id}",
                        "model_name": model_id,
                        "class": ChatGroq,
                        "args": {"temperature": 0.7},
                        "model_id_key": "model_name"
                    })

        info(f"✅ Fetched {len(groq_models)} Groq models dynamically")
        return groq_models

    except Exception as e:
        error(f"❌ Failed to fetch Groq models: {e}")
        info("🔄 Falling back to predefined Groq models")
        return get_fallback_groq_models()


def get_fallback_groq_models() -> List[Dict[str, Any]]:
    """
    Fallback Groq models if dynamic fetching fails.
    """
    all_models = [
        {"key": "groq/llama-3.1-70b-versatile", "model_name": "llama-3.1-70b-versatile",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/llama-3.1-8b-instant", "model_name": "llama-3.1-8b-instant",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/llama3-70b-8192", "model_name": "llama3-70b-8192",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/llama3-8b-8192", "model_name": "llama3-8b-8192",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/mixtral-8x7b-32768", "model_name": "mixtral-8x7b-32768",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/gemma2-9b-it", "model_name": "gemma2-9b-it",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
    ]
    return [model for model in all_models if is_text_model(model["model_name"], 'groq')]


def fetch_qwen_models(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch available Qwen models using the native Qwen provider.
    
    Args:
        api_key: Qwen API key for authentication
        
    Returns:
        List of model definition dictionaries
    """
    try:
        from models.qwen_provider import QwenModelProvider
        
        info("🔍 Fetching Qwen models using native provider...")
        
        # Create Qwen provider instance
        provider = QwenModelProvider(api_key=api_key)
        
        # Fetch models using the provider
        raw_models = provider.fetch_models()
        
        # Apply local text model filtering to ensure consistency
        qwen_models = [m for m in raw_models if is_text_model(m["model_name"], "qwen")]
        
        info(f"✅ Fetched {len(qwen_models)} Qwen models dynamically")
        return qwen_models
            
    except Exception as e:
        error(f"❌ Failed to fetch Qwen models: {e}")
        info("🔄 Falling back to an empty list as fallback models are deprecated.")
        return []


def get_model_definitions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get model definitions with dynamic fetching for OpenAI, xAI, Google, Anthropic, Groq, and Qwen models.
    
    This function fetches available models from each provider's API and caches the results
    to avoid frequent API calls. If API calls fail, it falls back to predefined model lists.
    Model definitions are filtered to include only text-based models suitable for content
    refinement tasks.
    
    Uses caching to avoid frequent API calls (cache duration: 1 hour).
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary mapping provider names to lists of
        model definition dictionaries. Each model definition contains:
            - key: Unique identifier for the model (e.g., "openai/gpt-4o")
            - model_name: Model identifier used by the provider's API
            - class: LangChain model class to instantiate
            - args: Default arguments for model initialization
            - model_id_key: Parameter name for model ID in constructor
            
    Example:
        >>> definitions = get_model_definitions()
        >>> definitions.keys()
        dict_keys(['openai', 'groq', 'google', 'anthropic', 'xai', 'qwen'])
        >>> len(definitions['openai'])
        4
=======
    Fetch model definitions from all providers with 1-hour caching.
    Falls back to predefined models when API calls fail.
<<<<<<< HEAD
>>>>>>> fb19d7bb9aeed507a8ce05166444c6711b3c931e
=======

    The cache is unused during normal app startup (initialize_models calls
<<<<<<< HEAD
    this once). It benefits tools or tests that call this function repeatedly
    in a single process.
=======
    this once). It benefits scripts/tools that call this function repeatedly
    in a single process (e.g. scripts/test_providers.py).
>>>>>>> 651ea15138a00ad88591d8db07a4193cdeeb3961
>>>>>>> dbd52812e78a3af8d74f3c2e744197f31a0192c3
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

    for provider_name, model_list in get_model_definitions().items():
        if not model_list:
            continue

        # api_key was already stored on the provider during get_model_definitions()
        api_key = model_list[0]["provider"].api_key

        if not api_key:
            warning(
                f"\n⚪ {provider_name.capitalize()} API Key not found, "
                f"skipping {provider_name} models."
            )
            for md in model_list:
                initialization_errors[md["key"]] = (
                    f"{provider_name.capitalize()} API Key not found."
                )
            continue

        info(f"\n-- Initializing {provider_name.capitalize()} models --")
        for md in model_list:
            model_key = md["key"]
            provider = md["provider"]
            try:
                initialized_models[model_key] = provider.build_callable(
                    md["model_name"], api_key
                )
                info(f"✅ Initialized {model_key}")
            except Exception as e:
                err = f"Failed to initialize {model_key}: {e}"
                initialization_errors[model_key] = err
                error(f"❌ {err}")

    info("\n--- Model Initialization Complete ---")
    if initialization_errors:
        warning("Some models failed to initialize. They will not be available for selection.")

    return initialized_models, initialization_errors
