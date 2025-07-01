#!/usr/bin/env python3
"""
Test Gemini models directly to find the most compatible one
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

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def test_gemini_model(model_name: str,
                      test_text: str = "Hello, please refine this text: I want to improve my writing."):
    """Test a specific Gemini model"""
    try:
        print(f"\n=== Testing {model_name} ===")

        # Create model instance
        model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )

        # Create simple chain
        prompt = ChatPromptTemplate.from_template(
            "Please refine the following text to make it clearer and more professional:\n\n{user_text}\n\nRefined text:"
        )
        chain = prompt | model | StrOutputParser()

        # Test the model
        print(f"Input: {test_text}")
        result = chain.invoke({"user_text": test_text})
        print(f"Output: {result}")
        print(f"Status: SUCCESS - {model_name} works correctly!")
        return True

    except Exception as e:
        print(f"Status: FAILED - {model_name} error: {str(e)}")
        return False


def main():
    """Test different Gemini models to find the most compatible ones"""
    print("=== Gemini Model Compatibility Test ===")

    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return

    print(f"Using Google API Key: {api_key[:10]}...")

    # Models to test, ordered by expected compatibility
    models_to_test = [
        "gemini-1.5-flash",  # Most stable
        "gemini-1.5-pro",  # Very stable
        "gemini-2.0-flash-exp",  # Experimental but should work
        "gemini-2.5-flash",  # Newer, might have issues
        "gemini-2.5-pro",  # Newest, likely has "thought" field issue
    ]

    test_text = "Hi there! I hope your doing well. This is a test message that needs some refinement."

    successful_models = []
    failed_models = []

    for model_name in models_to_test:
        if test_gemini_model(model_name, test_text):
            successful_models.append(model_name)
        else:
            failed_models.append(model_name)

    print("\n=== RESULTS SUMMARY ===")
    print(f"Successful models: {len(successful_models)}")
    for model in successful_models:
        print(f"  ✓ {model}")

    print(f"\nFailed models: {len(failed_models)}")
    for model in failed_models:
        print(f"  ✗ {model}")

    if successful_models:
        print(f"\nRECOMMENDATION: Use '{successful_models[0]}' for best compatibility")
        print(f"Model number in your program: Look for 'google/{successful_models[0]}' in the model list")
    else:
        print("\nERROR: No Gemini models are working. Check your API key and network connection.")


if __name__ == "__main__":
    main()
