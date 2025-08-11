#!/usr/bin/env python3
"""
Test if all required packages are properly installed
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_basic_imports():
    """Test if all basic packages can be imported"""
    print("=== Testing Basic Package Imports ===")

    tests = [
        ("python-dotenv", "import dotenv"),
        ("langchain-core", "from langchain_core.prompts import ChatPromptTemplate"),
        ("langchain-core", "from langchain_core.output_parsers import StrOutputParser"),
        ("langchain-openai", "from langchain_openai import ChatOpenAI"),
        ("langchain-groq", "from langchain_groq import ChatGroq"),
        ("langchain-google-genai", "from langchain_google_genai import ChatGoogleGenerativeAI"),
        ("langchain-anthropic", "from langchain_anthropic import ChatAnthropic"),
        ("langchain-xai", "from langchain_xai import ChatXAI"),
        ("google-generativeai", "import google.generativeai as genai"),
        ("openai", "from openai import OpenAI"),
        ("groq", "from groq import Groq"),
        ("anthropic", "import anthropic"),
        ("requests", "import requests"),
    ]

    passed = 0
    failed = 0

    for package_name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"✅ {package_name:25} - Import successful")
            passed += 1
        except ImportError as e:
            print(f"❌ {package_name:25} - Import failed: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {package_name:25} - Unexpected error: {e}")
            failed += 1

    print(f"\n=== Import Results ===")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")

    return failed == 0


def test_project_imports():
    """Test if project modules can be imported"""
    print("\n=== Testing Project Module Imports ===")

    try:
        from config.settings import API_KEYS, API_KEY_ARG_NAMES, ENABLE_STRICT_MODEL_FILTERING
        print("✅ config.settings - Import successful")
        print(f"   Strict filtering enabled: {ENABLE_STRICT_MODEL_FILTERING}")

        from models.model_loader import is_text_model, get_model_definitions
        print("✅ models.model_loader - Import successful")

        from prompts.refine_prompts import REFINE_TEXT_PROMPT
        print("✅ prompts.refine_prompts - Import successful")

        from utils.input_helpers import get_multiline_input
        print("✅ utils.input_helpers - Import successful")

        print("\n🎉 All project modules imported successfully!")
        return True

    except ImportError as e:
        print(f"❌ Project import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Unexpected error in project imports: {e}")
        return False


def test_model_filtering():
    """Test the enhanced model filtering"""
    print("\n=== Testing Enhanced Model Filtering ===")

    try:
        from models.model_loader import is_text_model

        # Test cases that should work
        test_cases = [
            ("gpt-4o", "openai", True),
            ("claude-3-5-sonnet", "anthropic", True),
            ("llama-guard-7b", "groq", False),  # Should be filtered
            ("text-davinci-edit-001", "openai", False),  # Should be filtered
            ("dall-e-3", "openai", False),  # Should be filtered
        ]

        all_passed = True
        for model_name, provider, expected in test_cases:
            result = is_text_model(model_name, provider)
            status = "✅" if result == expected else "❌"
            print(f"{status} {model_name:25} -> {result} (expected {expected})")
            if result != expected:
                all_passed = False

        if all_passed:
            print("\n🎉 Model filtering is working correctly!")
        else:
            print("\n⚠️  Some filtering tests failed.")

        return all_passed

    except Exception as e:
        print(f"❌ Model filtering test failed: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing AIRefiner Installation...\n")

    # Test basic imports
    basic_ok = test_basic_imports()

    # Test project imports
    project_ok = test_project_imports()

    # Test model filtering
    filtering_ok = test_model_filtering()

    print(f"\n=== Final Results ===")
    print(f"Basic packages: {'✅ OK' if basic_ok else '❌ Issues'}")
    print(f"Project modules: {'✅ OK' if project_ok else '❌ Issues'}")
    print(f"Model filtering: {'✅ OK' if filtering_ok else '❌ Issues'}")

    if basic_ok and project_ok and filtering_ok:
        print(f"\n🎉 🎉 🎉 INSTALLATION TEST PASSED! 🎉 🎉 🎉")
        print("Your AIRefiner is ready to run with:")
        print("✅ Dynamic model fetching from all 6 providers")
        print("✅ Enhanced intelligent model filtering")
        print("✅ All dependencies properly installed")
        print("\nYou can now run: python main.py")
    else:
        print(f"\n⚠️  Some issues detected. Check the failed imports above.")
