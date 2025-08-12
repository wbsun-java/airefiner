#!/usr/bin/env python3
"""
Test the enhanced model filtering for specialized models
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.model_loader import is_text_model

def test_specialized_model_filtering():
    """Test filtering of specialized models that shouldn't be used for text refinement"""
    
    print("=== Testing Enhanced Model Filtering ===")
    print("Testing specialized models that should be filtered out...\n")
    
    # Test cases for the problematic models
    specialized_models = [
        # Real-time models
        ("gpt-4o-realtime-preview", "openai", False, "Real-time conversation model"),
        ("gpt-4o-realtime-preview-2024-10-01", "openai", False, "Real-time conversation model"),
        ("gpt-4o-realtime-preview-2024-12-17", "openai", False, "Real-time conversation model"), 
        ("gpt-4o-realtime-preview-2025-06-03", "openai", False, "Real-time conversation model"),
        
        # Search models
        ("gpt-4o-search-preview", "openai", False, "Search integration model"),
        ("gpt-4o-search-preview-2025-03-11", "openai", False, "Search integration model"),
        
        # Transcribe models
        ("gpt-4o-transcribe", "openai", False, "Audio transcription model"),
        
        # Regular text models should still pass
        ("gpt-4o", "openai", True, "Standard chat model"),
        ("gpt-4o-mini", "openai", True, "Standard chat model"),
        ("claude-3-5-sonnet", "anthropic", True, "Standard chat model"),
    ]
    
    passed = 0
    failed = 0
    
    for model_name, provider, expected, description in specialized_models:
        result = is_text_model(model_name, provider)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"{status} | {model_name:40} | {description}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"      ↳ Expected: {expected}, Got: {result}")
    
    print(f"\n=== Results ===")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("🎉 All specialized model filtering working correctly!")
        print("✅ Real-time models are being filtered out")
        print("✅ Search models are being filtered out") 
        print("✅ Transcribe models are being filtered out")
        print("✅ Regular text models still pass through")
    else:
        print("⚠️  Some filtering tests failed.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_specialized_model_filtering()
    if success:
        print("\n🎉 Enhanced filtering is working perfectly!")
    else:
        print("\n⚠️  Filtering needs adjustment.")