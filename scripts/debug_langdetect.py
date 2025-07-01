#!/usr/bin/env python3
"""
Debug script to check langdetect installation and functionality
"""

print("=== Debugging Language Detection ===\n")

# Test 1: Check if langdetect is importable
print("1. Testing langdetect import...")
try:
    import langdetect

    print("✅ langdetect module imported successfully")
    print(f"   Version: {langdetect.__version__ if hasattr(langdetect, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ Failed to import langdetect: {e}")
    print("   Solution: pip install langdetect")
    exit(1)

# Test 2: Check specific functions
print("\n2. Testing langdetect functions...")
try:
    from langdetect import detect, LangDetectError

    print("✅ detect and LangDetectError imported successfully")
except ImportError as e:
    print(f"❌ Failed to import specific functions: {e}")
    exit(1)

# Test 3: Test basic detection
print("\n3. Testing basic language detection...")
test_texts = [
    "Hello, how are you?",
    "This is an English sentence.",
    "Good morning, have a nice day!"
]

for text in test_texts:
    try:
        detected = detect(text)
        print(f"✅ '{text}' -> {detected}")
    except Exception as e:
        print(f"❌ Failed to detect '{text}': {e}")

# Test 4: Test the TranslationHandler
print("\n4. Testing TranslationHandler...")
try:
    import sys
    import os

    # Add project root to path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from utils.translation_handler import TranslationHandler

    handler = TranslationHandler()
    test_text = "Hello, this is a test"

    result = handler.detect_language(test_text)
    print(f"✅ TranslationHandler.detect_language('{test_text}') -> {result}")

    translation_info = handler.determine_translation_direction(test_text)
    print(f"✅ Translation direction: {translation_info['source_language']} -> {translation_info['target_language']}")
    print(f"✅ Task ID: {translation_info['task_id']}")

except Exception as e:
    print(f"❌ TranslationHandler test failed: {e}")
    import traceback

    traceback.print_exc()

print("\n=== Debug Complete ===")
