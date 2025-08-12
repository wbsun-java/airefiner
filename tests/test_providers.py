#!/usr/bin/env python3
"""
Test AI provider dynamic fetching and integration
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_provider_fetching(provider_name, api_key_env_var, fetch_function, fallback_function):
    """Test dynamic fetching for a specific provider"""
    try:
        print(f"\n=== Testing {provider_name.title()} Dynamic Fetching ===")

        # Check API key
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            print(f"SKIPPED: {api_key_env_var} not found in environment")
            return False

        print(f"Using {provider_name.title()} API Key: {api_key[:10]}...")

        # Test fallback models first
        print(f"\nTesting fallback models...")
        fallback_models = fallback_function()
        print(f"Fallback models: {len(fallback_models)}")
        for model in fallback_models[:3]:  # Show first 3
            print(f"  - {model['key']} ({model['model_name']})")

        # Test dynamic fetching
        print(f"\nTesting dynamic fetching...")
        dynamic_models = fetch_function(api_key)
        print(f"Dynamic models: {len(dynamic_models)}")
        for model in dynamic_models[:3]:  # Show first 3
            print(f"  - {model['key']} ({model['model_name']})")

        print(f"✅ {provider_name.title()} fetching successful!")
        return True

    except Exception as e:
        print(f"❌ {provider_name.title()} fetching failed: {e}")
        return False


def main():
    """Test all provider dynamic fetching"""
    print("=== AI Provider Integration Test ===")
    print("Testing dynamic model fetching for all providers...\n")

    from models.model_loader import (
        fetch_openai_models, get_fallback_openai_models,
        fetch_google_models, get_fallback_google_models,
        fetch_anthropic_models, get_fallback_anthropic_models,
        fetch_groq_models, get_fallback_groq_models,
        fetch_xai_models, get_fallback_xai_models,
        fetch_qwen_models
    )

    providers = [
        ("openai", "OPENAI_API_KEY", fetch_openai_models, get_fallback_openai_models),
        ("google", "GOOGLE_API_KEY", fetch_google_models, get_fallback_google_models),
        ("anthropic", "ANTHROPIC_API_KEY", fetch_anthropic_models, get_fallback_anthropic_models),
        ("groq", "GROQ_API_KEY", fetch_groq_models, get_fallback_groq_models),
        ("xai", "XAI_API_KEY", fetch_xai_models, get_fallback_xai_models),
        ("qwen", "QWEN_API_KEY", fetch_qwen_models, lambda: [])  # Qwen has no fallback
    ]

    successful_providers = []
    failed_providers = []

    for provider_name, env_var, fetch_func, fallback_func in providers:
        if test_provider_fetching(provider_name, env_var, fetch_func, fallback_func):
            successful_providers.append(provider_name)
        else:
            failed_providers.append(provider_name)

    print(f"\n=== PROVIDER TEST RESULTS ===")
    print(f"✅ Successful providers: {len(successful_providers)}")
    for provider in successful_providers:
        print(f"  ✓ {provider.title()}")

    print(f"\n❌ Failed/Skipped providers: {len(failed_providers)}")
    for provider in failed_providers:
        print(f"  ✗ {provider.title()}")

    if successful_providers:
        print(f"\n🎉 {len(successful_providers)} providers are working correctly!")
        print("Your AIRefiner has access to multiple AI models for text processing.")
    else:
        print(f"\n⚠️  No providers are working. Check your API keys in .env file.")


if __name__ == "__main__":
    main()
