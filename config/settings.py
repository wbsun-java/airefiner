import os
# from dotenv import load_dotenv # No longer needed here, main.py loads it

# The .env file is loaded by main.py using load_dotenv()
# So os.getenv will work here.
print("config/settings.py: Attempting to access API keys from environment...")

# --- API Key Mappings ---
API_KEYS = {
    "openai": os.getenv('OPENAI_API_KEY'),
    "groq": os.getenv('GROQ_API_KEY'),
    "google": os.getenv('GOOGLE_API_KEY'),
    "anthropic": os.getenv('ANTHROPIC_API_KEY'),
    "xai": os.getenv('XAI_API_KEY'),
}

API_KEY_ARG_NAMES = {
    "openai": "openai_api_key",
    "groq": "groq_api_key",
    "google": "google_api_key", # For ChatGoogleGenerativeAI, it's 'google_api_key'
    "anthropic": "anthropic_api_key",
    "xai": "api_key", # As defined in your CustomGrokChatModel
}

print("config/settings.py: API Key mapping complete.")
if not any(API_KEYS.values()):
    print("WARNING (from config/settings.py): No API keys found in the environment for any provider.")
if not API_KEYS.get("xai"):
    print("INFO (from config/settings.py): XAI_API_KEY not found in environment. xAI models will be skipped if CustomGrokChatModel is used.")

# --- Define Available Tasks ---
TASKS = {
    "1": {"name": "Refine Text (Email, Article, etc.)", "id": "refine"},
    "2": {"name": "Translate: English -> Chinese", "id": "en_to_zh"},
    "3": {"name": "Translate: Chinese -> English", "id": "zh_to_en"},
}

# You can add other application-wide, non-sensitive configurations here
# DEFAULT_TEMPERATURE = 0.7
# MAX_RETRIES = 3