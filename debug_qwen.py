#!/usr/bin/env python3
"""
Debug script to test Qwen integration.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def debug_qwen_integration():
    """Debug Qwen integration issues."""
    print("🔍 Debugging Qwen Integration...")
    
    # Test 1: Check environment variable loading
    print("\n1. Environment Variable Loading:")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        qwen_key = os.getenv('QWEN_API_KEY')
        print(f"   Qwen API key loaded: {'Yes' if qwen_key else 'No'}")
        if qwen_key:
            print(f"   Key starts with: {qwen_key[:10]}...")
    except ImportError:
        print("   python-dotenv not available")
    
    # Test 2: Check settings loading
    print("\n2. Settings Loading:")
    try:
        from config.settings import API_KEYS, API_KEY_ARG_NAMES
        print(f"   Qwen in API_KEYS: {'qwen' in API_KEYS}")
        print(f"   Qwen in API_KEY_ARG_NAMES: {'qwen' in API_KEY_ARG_NAMES}")
        if 'qwen' in API_KEYS:
            print(f"   Qwen API key value: {'Present' if API_KEYS['qwen'] else 'None'}")
    except Exception as e:
        print(f"   Error loading settings: {e}")
    
    # Test 3: Check model loader functions
    print("\n3. Model Loader Functions:")
    try:
        with open('models/model_loader.py', 'r') as f:
            content = f.read()
            has_fetch_qwen = 'def fetch_qwen_models(' in content
            has_fallback_qwen = 'def get_fallback_qwen_models(' in content
            has_qwen_in_definitions = 'qwen_models = fetch_qwen_models(' in content
            print(f"   fetch_qwen_models function: {has_fetch_qwen}")
            print(f"   get_fallback_qwen_models function: {has_fallback_qwen}")
            print(f"   Qwen in model definitions: {has_qwen_in_definitions}")
    except Exception as e:
        print(f"   Error checking model loader: {e}")
    
    # Test 4: Check constants
    print("\n4. Constants:")
    try:
        with open('config/constants.py', 'r') as f:
            content = f.read()
            has_qwen_enum = 'QWEN = "qwen"' in content
            has_qwen_exclusions = 'ModelProvider.QWEN.value: []' in content
            print(f"   Qwen in ModelProvider enum: {has_qwen_enum}")
            print(f"   Qwen in provider exclusions: {has_qwen_exclusions}")
    except Exception as e:
        print(f"   Error checking constants: {e}")
    
    # Test 5: Test Qwen API call (if key is available)
    print("\n5. Qwen API Test:")
    qwen_key = os.getenv('QWEN_API_KEY')
    if qwen_key:
        try:
            import requests
            base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            headers = {
                "Authorization": f"Bearer {qwen_key}",
                "Content-Type": "application/json"
            }
            
            print(f"   Testing API call to: {base_url}/models")
            response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    models = [model.get('id', '') for model in data['data']]
                    print(f"   Found {len(models)} models")
                    print(f"   Sample models: {models[:3]}")
                else:
                    print(f"   Response data: {data}")
            else:
                print(f"   Error response: {response.text}")
                
        except Exception as e:
            print(f"   API test error: {e}")
    else:
        print("   No Qwen API key available for testing")
    
    print("\n🔍 Debug complete!")

if __name__ == "__main__":
    debug_qwen_integration() 