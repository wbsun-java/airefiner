#!/usr/bin/env python3
"""
Test script to verify Qwen model functionality
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_qwen_models():
    """Test Qwen model initialization and functionality"""
    print("🧪 Testing Qwen Model Functionality...")
    
    try:
        # Import the model loader
        from models.model_loader import initialize_models
        from config.settings import API_KEYS
        
        print("✅ Model loader imported successfully")
        
        # Check if Qwen API key is available
        if not API_KEYS.get("qwen"):
            print("⚠️  Qwen API key not found. Skipping Qwen tests.")
            return True
            
        # Initialize models
        print("\n📋 Initializing models...")
        models, errors = initialize_models()
        
        # Check for Qwen models
        qwen_models = [key for key in models.keys() if key.startswith('qwen/')]
        print(f"🎯 Qwen Models Available: {len(qwen_models)}")
        
        if not qwen_models:
            print("❌ No Qwen models found")
            return False
            
        # Test the first Qwen model
        first_qwen_model_key = qwen_models[0]
        print(f"🧪 Testing model: {first_qwen_model_key}")
        
        # Get the model instance
        model_instance = models[first_qwen_model_key]
        
        # Test a simple prompt
        print("📝 Testing simple prompt...")
        
        # Import required classes
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # Create a simple prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("user", "Say hello in English.")
        ])
        
        # Create chain
        chain = prompt | model_instance | StrOutputParser()
        
        # Execute the chain
        result = chain.invoke({})
        print(f"✅ Response: {result}")
        
        print("🎉 Qwen model test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Qwen models: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qwen_models()
    if success:
        print("\n✅ Qwen functionality test PASSED")
    else:
        print("\n❌ Qwen functionality test FAILED")
