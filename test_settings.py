#!/usr/bin/env python3
"""
Test script to check settings loading.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_settings():
    """Test if settings are loaded correctly."""
    print("🧪 Testing Settings Loading...")
    
    try:
        # Load environment variables first
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
        
        # Check if QWEN_API_KEY is in environment
        qwen_key = os.getenv('QWEN_API_KEY')
        print(f"🔑 QWEN_API_KEY in environment: {'Yes' if qwen_key else 'No'}")
        if qwen_key:
            print(f"   Key starts with: {qwen_key[:10]}...")
        
        # Import settings
        from config.settings import API_KEYS, API_KEY_ARG_NAMES
        
        print(f"\n📋 API_KEYS contents:")
        for provider, key in API_KEYS.items():
            has_key = 'Yes' if key else 'No'
            print(f"   {provider}: {has_key}")
        
        print(f"\n📋 API_KEY_ARG_NAMES contents:")
        for provider, arg_name in API_KEY_ARG_NAMES.items():
            print(f"   {provider}: {arg_name}")
        
        # Check specifically for Qwen
        print(f"\n🎯 Qwen Configuration:")
        print(f"   Qwen in API_KEYS: {'qwen' in API_KEYS}")
        print(f"   Qwen in API_KEY_ARG_NAMES: {'qwen' in API_KEY_ARG_NAMES}")
        print(f"   Qwen API key value: {'Yes' if API_KEYS.get('qwen') else 'No'}")
        print(f"   Qwen arg name: {API_KEY_ARG_NAMES.get('qwen', 'NOT FOUND')}")
        
    except Exception as e:
        print(f"❌ Error testing settings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_settings() 