# Import necessary standard LangChain classes
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

# --- Import Qwen Integration ---
try:
    from langchain_openai import ChatOpenAI as ChatQwen
except ImportError:
    ChatQwen = None
    print("WARNING: Could not import ChatOpenAI for Qwen integration")



try:
    from dotenv import load_dotenv
    load_dotenv()
    print("INFO: .env file loaded successfully.")
except ImportError:
    print("WARNING: python-dotenv not installed, .env file will not be loaded. Run: pip install python-dotenv")
# --- END OF ADDED SECTION ---

# --- Import Official xAI Integration ---
try:
    from langchain_xai import ChatXAI
except ImportError:
    ChatXAI = None
    print(
        "WARNING: Could not import ChatXAI from langchain-xai. Install with: pip install langchain-xai")

# Import configuration details (API keys and arg names)
from config.config_manager import get_config
from config.settings import ENABLE_STRICT_MODEL_FILTERING, CUSTOM_EXCLUDE_KEYWORDS

# Import for dynamic model fetching
from openai import OpenAI
import time
from typing import List, Dict, Any, Tuple

# Import for Google model fetching
try:
    import google.generativeai as genai
except ImportError:
    genai = None
    print("WARNING: google-generativeai not available for dynamic Google model fetching")

# Import for Anthropic model fetching
try:
    import anthropic
except ImportError:
    anthropic = None
    print("WARNING: anthropic not available for dynamic Anthropic model fetching")

# Import for Groq model fetching
try:
    from groq import Groq
except ImportError:
    Groq = None
    print("WARNING: groq not available for dynamic Groq model fetching")



import requests

# Global cache for model definitions
_model_cache = {}
_cache_timestamp = 0

# Import constants
from config.constants import CacheConfig, ModelFiltering
from utils.logger import info, warning, error


# --- Model Filtering Helper ---
def is_text_model(model_id: str, provider: str = "") -> bool:
    """
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

    # Add custom exclude keywords from settings
    non_text_keywords.extend([keyword.lower() for keyword in CUSTOM_EXCLUDE_KEYWORDS])

    # Explicitly exclude non-text models (image, video, robot, audio, etc.)
    strict_non_text_keywords = ['image', 'video', 'audio', 'robot', 'embed', 'dall-e', 'tts', 'whisper', 'vision-only']
    non_text_keywords.extend(strict_non_text_keywords)

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

        # Retry logic for fetching models
        max_retries = 3
        models = []
        for attempt in range(max_retries):
            try:
                # Convert to list to trigger the API call immediately
                models = list(genai.list_models())
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    warning(f"⚠️ Attempt {attempt + 1} failed to fetch Google models: {e}. Retrying...")
                    time.sleep(2)
                else:
                    raise e

        google_models = []
        for model in models:
            model_name = model.name.split('/')[-1] if '/' in model.name else model.name

            if is_text_model(model_name, 'google') and "gemini" in model_name.lower() and hasattr(model, 'supported_generation_methods'):
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
        
        # Filter using the strict is_text_model function to ensure only text models are loaded
        qwen_models = [m for m in raw_models if is_text_model(m['model_name'], 'qwen')]

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
    """
    global _model_cache, _cache_timestamp

    current_time = time.time()

    if _model_cache and (current_time - _cache_timestamp) < CacheConfig.DURATION_SECONDS:
        info("📋 Using cached model definitions")
        return _model_cache

    config = get_config()
    API_KEYS = config.api_config.get_api_keys()

    openai_models = []
    if API_KEYS.get("openai"):
        openai_models = fetch_openai_models(API_KEYS["openai"])
    else:
        warning("⚪ OpenAI API key not found, using fallback models")
        openai_models = get_fallback_openai_models()

    xai_models = []
    if API_KEYS.get("xai"):
        xai_models = fetch_xai_models(API_KEYS["xai"])
    else:
        warning("⚪ xAI API key not found, using fallback Grok models")
        xai_models = get_fallback_xai_models()

    google_models = []
    if API_KEYS.get("google"):
        google_models = fetch_google_models(API_KEYS["google"])
    else:
        warning("⚪ Google API key not found, using fallback Gemini models")
        google_models = get_fallback_google_models()

    anthropic_models = []
    if API_KEYS.get("anthropic"):
        anthropic_models = fetch_anthropic_models(API_KEYS["anthropic"])
    else:
        warning("⚪ Anthropic API key not found, using fallback Claude models")
        anthropic_models = get_fallback_anthropic_models()

    groq_models = []
    if API_KEYS.get("groq"):
        groq_models = fetch_groq_models(API_KEYS["groq"])
    else:
        warning("⚪ Groq API key not found, using fallback models")
        groq_models = get_fallback_groq_models()

    qwen_models = []
    if API_KEYS.get("qwen"):
        qwen_models = fetch_qwen_models(API_KEYS["qwen"])
    else:
        warning("⚪ Qwen API key not found, using fallback models")
        qwen_models = []

    model_definitions = {
        "openai": openai_models,
        "groq": groq_models,
        "google": google_models,
        "anthropic": anthropic_models,
        "xai": xai_models,
        "qwen": qwen_models,
    }

    _model_cache = model_definitions
    _cache_timestamp = current_time
    info(f"💾 Model definitions cached for {CacheConfig.CACHE_DURATION_MINUTES} minutes")
    info(f"📊 Total models after filtering: {sum(len(models) for models in model_definitions.values())}")

    return model_definitions

# --- initialize_models Function (MODIFIED) ---
def initialize_models() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Initialize all AI models defined in MODEL_DEFINITIONS based on available API keys.
    
    This function dynamically fetches model definitions from various AI providers,
    initializes model instances using the appropriate LangChain classes, and handles
    errors gracefully by providing fallback models when API calls fail.
    
    Returns:
        Tuple containing:
            - initialized_models (Dict[str, Any]): Dictionary mapping model keys to 
              initialized LangChain model instances
            - initialization_errors (Dict[str, str]): Dictionary mapping model keys
              to error messages for models that failed to initialize
              
    Example:
        >>> models, errors = initialize_models()
        >>> len(models)
        15
        >>> 'openai/gpt-4o' in models
        True
        >>> if errors:
        ...     print(f"Failed to initialize: {list(errors.keys())}")
    """
    initialized_models = {}
    initialization_errors = {}

    info("\n--- Initializing Models (from models/model_loader.py) ---")

    config = get_config()
    API_KEYS = config.api_config.get_api_keys()
    API_KEY_ARG_NAMES = config.api_config.api_key_arg_names

    MODEL_DEFINITIONS = get_model_definitions()

    for provider, model_list in MODEL_DEFINITIONS.items():
        api_key = API_KEYS.get(provider)
        api_key_arg_name = API_KEY_ARG_NAMES.get(provider)

        if not api_key_arg_name:
            warning(f"\n⚠️ Skipping provider '{provider}': Not configured in config_manager.py (api_key_arg_names).")
            for model_def in model_list:
                initialization_errors[model_def["key"]] = f"Provider '{provider}' not configured in api_key_arg_names."
            continue

        if provider == "xai" and ChatXAI is None:
            warning(f"\n⚪ Skipping xAI models: ChatXAI class not imported. Install with: pip install langchain-xai")
            for model_def in model_list:
                initialization_errors[model_def["key"]] = "ChatXAI class not available. Install langchain-xai package."
            continue

        if provider == "qwen" and ChatQwen is None:
            warning(f"\n⚪ Skipping Qwen models: ChatQwen class not imported.")
            for model_def in model_list:
                initialization_errors[model_def["key"]] = "ChatQwen class not available."
            continue



        if not api_key:
            warning(
                f"\n⚪ {provider.capitalize()} API Key not found in environment (via config/settings.py), skipping {provider} models.")
            for model_def in model_list:
                initialization_errors[model_def["key"]] = f"{provider.capitalize()} API Key not found."
            continue

        info(f"\n-- Initializing {provider.capitalize()} models --")
        for model_def in model_list:
            model_key = model_def["key"]
            model_identifier_value = model_def["model_name"]
            model_class = model_def["class"]
            constructor_id_param_name = model_def.get("model_id_key")

            if model_class is None and provider == "xai":
                error_msg = f"Class definition missing for {model_key} (ChatXAI likely failed to import)."
                initialization_errors[model_key] = error_msg
                warning(f"⚪ Skipping {model_key}: {error_msg}")
                continue
            elif model_class is None:
                error_msg = f"Class definition missing for {model_key}."
                initialization_errors[model_key] = error_msg
                warning(f"⚪ Skipping {model_key}: {error_msg}")
                continue

            if not constructor_id_param_name:
                error_msg = f"Configuration error: 'model_id_key' missing for {model_key} in MODEL_DEFINITIONS."
                initialization_errors[model_key] = error_msg
                warning(f"⚪ Skipping {model_key}: {error_msg}")
                continue

            model_args_from_def = model_def["args"].copy()
            model_args_from_def[api_key_arg_name] = api_key

            try:
                constructor_kwargs = {constructor_id_param_name: model_identifier_value}
                final_constructor_args = {**constructor_kwargs, **model_args_from_def}

                initialized_models[model_key] = model_class(**final_constructor_args)
                info(f"✅ Initialized {model_key}")

            except Exception as e:
                error_msg = f"Failed to initialize {model_key}: {e}"
                initialization_errors[model_key] = error_msg
                error(f"❌ {error_msg}")

    info("\n--- Model Initialization Complete ---")
    if initialization_errors:
        warning("\n--- Initialization Warnings ---")
        warning("Some models failed to initialize (check errors above). They will not be available for selection.")

    return initialized_models, initialization_errors
