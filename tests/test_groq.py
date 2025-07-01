#!/usr/bin/env python3
"""
Test Groq dynamic model fetching
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


def test_groq_fetching():
    """Test Groq model fetching"""
    try:
        print("=== Testing Groq Dynamic Fetching ===")

        # Check API key
        from config.settings import API_KEYS
        api_key = API_KEYS.get("groq")
        if not api_key:
            print("ERROR: GROQ_API_KEY not found in environment")
            return

        print(f"Using Groq API Key: {api_key[:10]}...")

        # Test fallback models first
        from models.model_loader import get_fallback_groq_models
        fallback_models = get_fallback_groq_models()
        print(f"\nFallback models: {len(fallback_models)}")
        for model in fallback_models:
            print(f"  - {model['key']} ({model['model_name']})")

        # Test dynamic fetching
        print("\nTesting dynamic fetching...")
        from models.model_loader import fetch_groq_models
        dynamic_models = fetch_groq_models(api_key)
        print(f"Dynamic models: {len(dynamic_models)}")
        for model in dynamic_models:
            print(f"  - {model['key']} ({model['model_name']})")

        print("\n=== Test Completed ===")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    success = test_groq_fetching()
    if success:
        print("Groq dynamic fetching is working!")
    else:
        print("Groq dynamic fetching failed.")


if __name__ == "__main__":
    main()
