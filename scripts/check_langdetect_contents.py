#!/usr/bin/env python3
"""
Check what's actually available in langdetect package
"""

import langdetect

print("=== Checking langdetect package contents ===")

print("Available attributes:")
for attr in dir(langdetect):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\nTesting basic detect function:")
try:
    result = langdetect.detect("Hello world")
    print(f"✅ Basic detect works: {result}")
except Exception as e:
    print(f"❌ Basic detect failed: {e}")
    print(f"   Exception type: {type(e)}")

print("\nTesting with error handling:")
try:
    result = langdetect.detect("")  # Should cause an error
    print(f"Empty string result: {result}")
except Exception as e:
    print(f"✅ Empty string correctly raises: {type(e).__name__}: {e}")

print("\nChecking langdetect.lang_detect_exception:")
try:
    from langdetect.lang_detect_exception import LangDetectException

    print("✅ Found LangDetectException in lang_detect_exception module")
except ImportError as e:
    print(f"❌ LangDetectException not found: {e}")

print("\nChecking direct module import:")
try:
    import langdetect.lang_detect_exception as lde

    print(f"Available in lang_detect_exception: {dir(lde)}")
except ImportError as e:
    print(f"❌ Can't import lang_detect_exception: {e}")
