#!/usr/bin/env python3
"""
Test script to see what models are being loaded.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_model_loading():
    """Test model loading to see if Qwen models are included."""
    print("🧪 Testing Model Loading...")
    
    try:
        # Import the model loader
        from models.model_loader import get_model_definitions
        
        print("✅ Model loader imported successfully")
        
        # Get model definitions
        print("\n📋 Fetching model definitions...")
        model_definitions = get_model_definitions()
        
        print(f"✅ Found {len(model_definitions)} providers")
        
        # Check each provider
        for provider, models in model_definitions.items():
            print(f"\n🔍 Provider: {provider}")
            print(f"   Models count: {len(models)}")
            
            if models:
                print(f"   Sample models:")
                for i, model in enumerate(models[:3]):  # Show first 3 models
                    print(f"     {i+1}. {model.get('key', 'Unknown')}")
                if len(models) > 3:
                    print(f"     ... and {len(models) - 3} more")
            else:
                print("   No models found")
        
        # Specifically check for Qwen
        if 'qwen' in model_definitions:
            qwen_models = model_definitions['qwen']
            print(f"\n🎯 Qwen Models Found: {len(qwen_models)}")
            for model in qwen_models:
                print(f"   - {model.get('key', 'Unknown')}")
        else:
            print("\n❌ No Qwen provider found in model definitions")
            
    except Exception as e:
        print(f"❌ Error testing model loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_loading() 