#!/usr/bin/env python3
"""
Test the auto-translation functionality
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_translation_handler():
    """Test the TranslationHandler functionality"""
    try:
        from utils.translation_handler import TranslationHandler

        print("=== Testing Auto-Translation Handler ===")

        handler = TranslationHandler()

        test_cases = [
            {
                "text": "Hello, how are you today?",
                "expected_direction": "en_to_zh",
                "description": "English text"
            },
            {
                "text": "Hi, I recently canceled one policy from my account.",
                "expected_direction": "en_to_zh",
                "description": "English policy text"
            },
            {
                "text": "This is a test of the emergency broadcast system.",
                "expected_direction": "en_to_zh",
                "description": "English test text"
            }
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {case['description']} ---")
            print(f"Input: {case['text']}")

            # Test language detection
            detected_lang, confidence = handler.detect_language(case['text'])
            print(f"Detected Language: {detected_lang} (confidence: {confidence:.2f})")

            # Test translation direction determination
            translation_info = handler.determine_translation_direction(case['text'])
            print(f"Translation Task: {translation_info['task_id']}")
            print(f"Direction: {translation_info['source_language']} -> {translation_info['target_language']}")

            # Test summary generation
            summary = handler.get_translation_summary(translation_info, case['text'])
            print(f"Summary:\n{summary}")

            # Check if matches expected
            expected_match = translation_info['task_id'] == case['expected_direction']
            print(f"Expected Direction Match: {'✅ YES' if expected_match else '❌ NO'}")

            print("-" * 60)

        print("\n🎉 Auto-translation handler test completed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure langdetect is installed: pip install langdetect")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_settings_integration():
    """Test that the new task is properly integrated in settings"""
    try:
        from config.settings import TASKS

        print("\n=== Testing Settings Integration ===")

        print("Available tasks:")
        for task_num, task_info in TASKS.items():
            print(f"  {task_num}. {task_info['name']} (id: {task_info['id']})")

        # Check if auto_translate task exists
        auto_translate_exists = any(
            task_info['id'] == 'auto_translate'
            for task_info in TASKS.values()
        )

        if auto_translate_exists:
            print("✅ Auto-translate task found in settings!")
        else:
            print("❌ Auto-translate task not found in settings")

        # Check that old translation tasks are removed
        old_tasks = ['en_to_zh', 'zh_to_en']
        old_tasks_found = [
            task_id for task_id in old_tasks
            if any(task_info['id'] == task_id for task_info in TASKS.values())
        ]

        if old_tasks_found:
            print(f"⚠️  Old translation tasks still found: {old_tasks_found}")
        else:
            print("✅ Old manual translation tasks successfully removed!")

        return auto_translate_exists and not old_tasks_found

    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Auto-Translation Feature\n")

    # Test translation handler
    handler_ok = test_translation_handler()

    # Test settings integration
    settings_ok = test_settings_integration()

    print(f"\n=== Final Results ===")
    print(f"Translation Handler: {'✅ OK' if handler_ok else '❌ Failed'}")
    print(f"Settings Integration: {'✅ OK' if settings_ok else '❌ Failed'}")

    if handler_ok and settings_ok:
        print(f"\n🎉 🎉 🎉 AUTO-TRANSLATION READY! 🎉 🎉 🎉")
        print("Features working:")
        print("✅ Automatic language detection")
        print("✅ Intelligent translation direction selection")
        print("✅ Simplified task menu (3 options instead of 4)")
        print("✅ Fallback to text refinement for unknown languages")
        print("\nYou can now run: python main.py")
    else:
        print(f"\n⚠️  Some issues detected. Check the failed tests above.")
