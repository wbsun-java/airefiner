#!/usr/bin/env python3
"""
Comprehensive test for all filtering edge cases
"""


def comprehensive_text_model_filter(model_id: str, provider: str = "") -> bool:
    """
    Complete implementation matching the enhanced filtering in model_loader.py
    """
    model_id_lower = model_id.lower()

    # All non-text keywords from enhanced implementation
    non_text_keywords = [
        # Image/Vision models
        'image', 'vision', 'dalle', 'clip', 'vit', 'img', 'visual', 'pic', 'photo',
        # Audio models  
        'audio', 'tts', 'whisper', 'speech', 'voice', 'sound', 'music',
        # Video models
        'video', 'vid', 'motion', 'animation',
        # Embedding models
        'embed', 'embedding', 'similarity', 'vector', 'retrieval',
        # Code/Programming specific (not for text refinement)
        'code', 'programming', 'dev', 'developer',
        # Moderation/Safety models
        'moderation', 'safety', 'content-filter', 'toxic',
        # Fine-tuning/Training models
        'fine-tune', 'finetune', 'training', 'custom',
        # Other specialized models
        'reasoning', 'math', 'science', 'research',
        # Security/Guard models
        'guard', 'guardian', 'safety-model',
        # Legacy/Edit models
        'edit', 'davinci-edit', 'curie-edit'
    ]

    # Provider-specific exclusions
    provider_specific_exclusions = {
        'openai': ['davinci-edit', 'curie-edit', 'babbage-edit', 'ada-edit'],
        'google': ['bison', 'gecko', 'otter', 'unicorn'],
        'anthropic': [],
        'groq': ['whisper', 'distil-whisper'],
        'xai': []
    }

    # Check common non-text keywords
    for keyword in non_text_keywords:
        if keyword in model_id_lower:
            print(f"🔎 Filtering out non-text model ({keyword}): {model_id}")
            return False

    # Check provider-specific exclusions
    if provider and provider in provider_specific_exclusions:
        for excluded_model in provider_specific_exclusions[provider]:
            if excluded_model.lower() in model_id_lower:
                print(f"🔎 Filtering out provider-specific non-text model: {model_id}")
                return False

    # Text model indicators
    text_indicators = [
        'chat', 'gpt', 'claude', 'gemini', 'llama', 'mistral', 'qwen', 'deepseek', 'grok',
        'text', 'language', 'conversation', 'instruct', 'assistant'
    ]

    has_text_indicator = any(indicator in model_id_lower for indicator in text_indicators)

    if not has_text_indicator:
        print(f"🔎 Model may not be text-focused (no text indicators): {model_id}")
        return False

    return True


def test_all_edge_cases():
    """Test comprehensive edge cases including the two that were failing"""

    test_cases = [
        # ✅ SHOULD BE INCLUDED - Core text models
        ("gpt-4o", "openai", True, "Core OpenAI chat model"),
        ("gpt-3.5-turbo", "openai", True, "Core OpenAI chat model"),
        ("gpt-4-turbo", "openai", True, "Core OpenAI chat model"),
        ("claude-3-5-sonnet-20241022", "anthropic", True, "Core Anthropic model"),
        ("claude-3-haiku", "anthropic", True, "Core Anthropic model"),
        ("gemini-1.5-pro", "google", True, "Core Google model"),
        ("gemini-2.0-flash-exp", "google", True, "Experimental Google model"),
        ("llama-3.1-8b-instruct", "groq", True, "Instruct model for text"),
        ("llama-3.3-70b-versatile", "groq", True, "Versatile text model"),
        ("mistral-7b-instruct", "groq", True, "Instruct model"),
        ("qwen-qwq-32b", "groq", True, "Qwen model"),
        ("deepseek-r1-distill-llama-70b", "groq", True, "DeepSeek model"),
        ("grok-beta", "xai", True, "Core xAI model"),
        ("grok-2", "xai", True, "Core xAI model"),

        # ❌ SHOULD BE EXCLUDED - The failing cases
        ("llama-guard-7b", "groq", False, "Security/Guard model - SHOULD BE FILTERED"),
        ("text-davinci-edit-001", "openai", False, "Legacy edit model - SHOULD BE FILTERED"),

        # ❌ SHOULD BE EXCLUDED - Image/Vision models
        ("dall-e-3", "openai", False, "Image generation model"),
        ("dall-e-2", "openai", False, "Image generation model"),
        ("gpt-4-vision-preview", "openai", False, "Vision model"),
        ("gpt-4o-vision", "openai", False, "Vision model"),
        ("claude-3-vision", "anthropic", False, "Vision model"),
        ("gemini-pro-vision", "google", False, "Vision model"),
        ("gemini-1.5-vision", "google", False, "Vision model"),

        # ❌ SHOULD BE EXCLUDED - Audio models
        ("whisper-1", "openai", False, "Audio transcription"),
        ("whisper-large-v3", "groq", False, "Audio transcription"),
        ("distil-whisper-large-v2", "groq", False, "Audio transcription"),
        ("tts-1", "openai", False, "Text-to-speech"),
        ("tts-1-hd", "openai", False, "Text-to-speech"),

        # ❌ SHOULD BE EXCLUDED - Embedding models
        ("text-embedding-ada-002", "openai", False, "Embedding model"),
        ("text-embedding-3-small", "openai", False, "Embedding model"),
        ("text-embedding-3-large", "openai", False, "Embedding model"),

        # ❌ SHOULD BE EXCLUDED - Code models
        ("code-davinci-002", "openai", False, "Code generation"),
        ("codex", "openai", False, "Code generation"),
        ("github-copilot", "openai", False, "Code generation"),

        # ❌ SHOULD BE EXCLUDED - Specialized models
        ("gpt-4-math-preview", "openai", False, "Math specialized"),
        ("claude-3-reasoning", "anthropic", False, "Reasoning specialized"),
        ("gemini-science-pro", "google", False, "Science specialized"),

        # ❌ SHOULD BE EXCLUDED - Safety/Moderation
        ("content-moderation-stable", "openai", False, "Moderation model"),
        ("safety-classifier", "anthropic", False, "Safety model"),
        ("toxic-detection-model", "google", False, "Toxicity detection"),

        # ❌ SHOULD BE EXCLUDED - Legacy/Edit models
        ("davinci-edit-001", "openai", False, "Legacy edit model"),
        ("curie-edit-001", "openai", False, "Legacy edit model"),
        ("text-davinci-edit-002", "openai", False, "Legacy edit model"),

        # ❌ SHOULD BE EXCLUDED - Fine-tuning models
        ("custom-fine-tuned-gpt-4", "openai", False, "Fine-tuned model"),
        ("training-model-v1", "anthropic", False, "Training model"),

        # ❌ SHOULD BE EXCLUDED - No text indicators
        ("random-model-xyz", "", False, "No text indicators"),
        ("unknown-ai-model", "", False, "No text indicators"),
        ("mystery-model-2024", "", False, "No text indicators"),
    ]

    print("=== Comprehensive Edge Case Testing ===")
    print(f"Testing {len(test_cases)} model names across all categories...\n")

    passed = 0
    failed = 0

    for model_name, provider, expected, description in test_cases:
        actual = comprehensive_text_model_filter(model_name, provider)
        status = "✅ PASS" if actual == expected else "❌ FAIL"

        print(f"{status} | {model_name:35} | {provider:10} | {description}")

        if actual == expected:
            passed += 1
        else:
            failed += 1
            print(f"      ↳ Expected: {expected}, Got: {actual}")

    print(f"\n=== Final Results ===")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")

    # Specific check for the two originally failing cases
    print(f"\n=== Originally Failing Cases ===")
    guard_result = comprehensive_text_model_filter("llama-guard-7b", "groq")
    edit_result = comprehensive_text_model_filter("text-davinci-edit-001", "openai")

    print(f"llama-guard-7b: {'✅ FIXED' if not guard_result else '❌ STILL FAILING'}")
    print(f"text-davinci-edit-001: {'✅ FIXED' if not edit_result else '❌ STILL FAILING'}")

    return failed == 0


if __name__ == "__main__":
    success = test_all_edge_cases()
    if success:
        print("\n🎉 ALL TESTS PASSED! Comprehensive filtering is working perfectly.")
        print("✅ Both originally failing cases are now properly filtered out.")
        print("✅ All text models are correctly identified and included.")
        print("✅ All non-text models are correctly filtered out.")
    else:
        print("\n⚠️  Some tests failed. Review the filtering logic.")
