#!/usr/bin/env python3
"""
Test script to see what models are being initialized.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_model_initialization():
    """Test model initialization to see if Qwen models are included."""
    print("🧪 Testing Model Initialization...")
    
    try:
        # Import the model loader
        from models.model_loader import initialize_models
        
        print("✅ Model loader imported successfully")
        
        # Initialize models
        print("\n📋 Initializing models...")
        models, errors = initialize_models()
        
        print(f"✅ Initialized {len(models)} models")
        print(f"❌ Failed to initialize {len(errors)} models")
        
        # Check for Qwen models
        qwen_models = [key for key in models.keys() if key.startswith('qwen/')]
        print(f"\n🎯 Qwen Models Initialized: {len(qwen_models)}")
        for model in qwen_models:
            print(f"   - {model}")
        
        # Check for Qwen errors
        qwen_errors = [key for key in errors.keys() if key.startswith('qwen/')]
        print(f"\n❌ Qwen Models Failed: {len(qwen_errors)}")
        for model in qwen_errors:
            print(f"   - {model}: {errors[model]}")
        
        # Show all models by provider
        print(f"\n📊 All Models by Provider:")
        providers = {}
        for model_key in models.keys():
            provider = model_key.split('/')[0] if '/' in model_key else 'unknown'
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model_key)
        
        for provider, model_list in sorted(providers.items()):
            print(f"   {provider.capitalize()}: {len(model_list)} models")
            for model in sorted(model_list)[:3]:  # Show first 3
                print(f"     - {model}")
            if len(model_list) > 3:
                print(f"     ... and {len(model_list) - 3} more")
        
        # Show all errors
        if errors:
            print(f"\n❌ All Initialization Errors:")
            for model, error in errors.items():
                print(f"   - {model}: {error}")
            
    except Exception as e:
        print(f"❌ Error testing model initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_initialization()
