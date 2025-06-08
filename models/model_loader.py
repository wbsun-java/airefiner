# Import necessary standard LangChain classes
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# --- Import Custom Classes ---
try:
    # Import the specific custom class from within the 'models' package
    from .custom_models import CustomGrokChatModel
except ImportError:
    CustomGrokChatModel = None  # Handle if custom_models.py doesn't exist
    print(
        "WARNING: Could not import CustomGrokChatModel from models.custom_models.py. xAI models may not be available.")

# Import configuration details (API keys and arg names)
# These are loaded in config.settings and imported into main.py,
# then passed or accessed by model_loader.
# For simplicity here, we'll import them directly from config.settings
# assuming main.py has already ensured .env is loaded.
from config.settings import API_KEYS, API_KEY_ARG_NAMES

# --- MODEL_DEFINITIONS (with model_id_key) ---
MODEL_DEFINITIONS = {
    "openai": [
        {"key": "openai/gpt-4.1-mini", "model_name": "gpt-4.1-mini", "class": ChatOpenAI, "args": {"temperature": 0.7},
         "model_id_key": "model_name"},
        {"key": "openai/gpt-4.5-preview-2025-02-27", "model_name": "gpt-4.5-preview-2025-02-27", "class": ChatOpenAI,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "openai/gpt-4.5-preview", "model_name": "gpt-4.5-preview", "class": ChatOpenAI,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "openai/gpt-4.1-nano-2025-04-14", "model_name": "gpt-4.1-nano-2025-04-14", "class": ChatOpenAI,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
    ],
    "groq": [
        {"key": "groq/meta-llama/llama-guard-4-12b", "model_name": "meta-llama/llama-guard-4-12b", "class": ChatGroq,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
         "model_name": "meta-llama/llama-4-scout-17b-16e-instruct", "class": ChatGroq, "args": {"temperature": 0.7},
         "model_id_key": "model_name"},
        {"key": "groq/deepseek-r1-distill-llama-70b", "model_name": "deepseek-r1-distill-llama-70b", "class": ChatGroq,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/llama-4-maverick-17b", "model_name": "meta-llama/llama-4-maverick-17b-128e-instruct",
         "class": ChatGroq, "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/llama-3.3-70b-versatile", "model_name": "llama-3.3-70b-versatile", "class": ChatGroq,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "groq/qwen-qwq-32b", "model_name": "qwen-qwq-32b", "class": ChatGroq, "args": {"temperature": 0.7},
         "model_id_key": "model_name"},
    ],
    "google": [
        {"key": "google/gemini-2.5-flash-preview-04-17", "model_name": "gemini-2.5-flash-preview-04-17",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemini-2.5-pro-preview-03-25", "model_name": "gemini-2.5-pro-preview-03-25",
         "class": ChatGoogleGenerativeAI, "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemma-3-12b-it", "model_name": "gemma-3-12b-it", "class": ChatGoogleGenerativeAI,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "google/gemini-2.0-flash-exp", "model_name": "gemini-2.0-flash-exp", "class": ChatGoogleGenerativeAI,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
    ],
    "anthropic": [
        {"key": "anthropic/claude-3-5-sonnet", "model_name": "claude-3-5-sonnet-20241022", "class": ChatAnthropic,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/claude-3.7-sonnet", "model_name": "claude-3-7-sonnet-20250219", "class": ChatAnthropic,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/Claude Sonnet 4", "model_name": "claude-sonnet-4-20250514", "class": ChatAnthropic,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"},
        {"key": "anthropic/Claude Opus 4", "model_name": "claude-opus-4-20250514", "class": ChatAnthropic,
         "args": {"temperature": 0.7}, "model_id_key": "model_name"}
    ],
    "xai": [
        {"key": "xAI/Grok 3 Beta", "model_name": "grok-3-beta", "class": CustomGrokChatModel,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "xAI/grok-3 mini beta", "model_name": "grok-3-mini-beta", "class": CustomGrokChatModel,
         "args": {"temperature": 0.7}, "model_id_key": "model"},
        {"key": "xAI/Grok 3 Mini Beta (Fast Model)", "model_name": "grok-3-mini-fast-beta",
         "class": CustomGrokChatModel, "args": {"temperature": 0.7}, "model_id_key": "model"},
    ],
}


# --- initialize_models Function (MODIFIED) ---
def initialize_models():
    """
    Initializes all models defined in MODEL_DEFINITIONS based on available API keys.
    Returns: tuple: (initialized_models dict, initialization_errors dict)
    """
    initialized_models = {}
    initialization_errors = {}

    print("\n--- Initializing Models (from models/model_loader.py) ---")

    for provider, model_list in MODEL_DEFINITIONS.items():
        api_key = API_KEYS.get(provider)
        api_key_arg_name = API_KEY_ARG_NAMES.get(provider)

        if not api_key_arg_name:
            print(f"\n⚠️ Skipping provider '{provider}': Not configured in config/settings.py (API_KEY_ARG_NAMES).")
            # Log errors for all models under this unconfigured provider
            for model_def in model_list:
                initialization_errors[model_def["key"]] = f"Provider '{provider}' not configured in API_KEY_ARG_NAMES."
            continue

        if provider == "xai" and CustomGrokChatModel is None:
            print(f"\n⚪ Skipping xAI models: CustomGrokChatModel class not imported.")
            for model_def in model_list:
                initialization_errors[model_def["key"]] = "CustomGrokChatModel class not available (import failed)."
            continue

        if not api_key:
            print(
                f"\n⚪ {provider.capitalize()} API Key not found in environment (via config/settings.py), skipping {provider} models.")
            for model_def in model_list:
                initialization_errors[model_def["key"]] = f"{provider.capitalize()} API Key not found."
            continue

        print(f"\n-- Initializing {provider.capitalize()} models --")
        for model_def in model_list:
            model_key = model_def["key"]
            model_identifier_value = model_def["model_name"]
            model_class = model_def["class"]
            constructor_id_param_name = model_def.get("model_id_key")

            if model_class is None and provider == "xai":  # Should have been caught by CustomGrokChatModel is None
                error_msg = f"Class definition missing for {model_key} (CustomGrokChatModel likely failed to import)."
                initialization_errors[model_key] = error_msg
                print(f"⚪ Skipping {model_key}: {error_msg}")
                continue
            elif model_class is None:  # General case, though less likely with explicit imports
                error_msg = f"Class definition missing for {model_key}."
                initialization_errors[model_key] = error_msg
                print(f"⚪ Skipping {model_key}: {error_msg}")
                continue

            if not constructor_id_param_name:
                error_msg = f"Configuration error: 'model_id_key' missing for {model_key} in MODEL_DEFINITIONS."
                initialization_errors[model_key] = error_msg
                print(f"⚪ Skipping {model_key}: {error_msg}")
                continue

            model_args_from_def = model_def["args"].copy()
            model_args_from_def[api_key_arg_name] = api_key

            try:
                constructor_kwargs = {constructor_id_param_name: model_identifier_value}
                final_constructor_args = {**constructor_kwargs, **model_args_from_def}

                initialized_models[model_key] = model_class(**final_constructor_args)
                print(f"✅ Initialized {model_key}")

            except Exception as e:
                error_msg = f"Failed to initialize {model_key}: {e}"
                initialization_errors[model_key] = error_msg
                print(f"❌ {error_msg}")

    print("\n--- Model Initialization Complete ---")
    if initialization_errors:
        print("\n--- Initialization Warnings ---")
        print("Some models failed to initialize (check errors above). They will not be available for selection.")
        # for key, err in initialization_errors.items(): # Optional: print detailed errors again
        #     if key not in initialized_models:
        #         print(f"  - {key}: {err}")

    return initialized_models, initialization_errors