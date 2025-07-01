#!/usr/bin/env python3
"""
Translation Handler - Automatic language detection and translation
"""

import os
import sys
from typing import Dict, Tuple

try:
    from langdetect import detect
    from langdetect.lang_detect_exception import LangDetectException

    LangDetectError = LangDetectException  # Alias for compatibility
except ImportError:
    detect = None
    LangDetectError = Exception
    print("WARNING: langdetect not available. Install with: pip install langdetect")

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from prompts.translate_prompts import TRANSLATE_EN_TO_ZH_PROMPT, TRANSLATE_ZH_TO_EN_PROMPT


class TranslationHandler:
    """
    Handles automatic language detection and translation between English and Chinese
    """

    def __init__(self):
        """Initialize the translation handler"""
        self.supported_languages = {
            'en': 'English',
            'zh-cn': 'Simplified Chinese',
            'zh-tw': 'Traditional Chinese',
            'zh': 'Chinese'  # Generic Chinese
        }

        # Map detected languages to our translation tasks
        self.language_mapping = {
            'en': 'english',
            'zh-cn': 'chinese',
            'zh-tw': 'chinese',
            'zh': 'chinese'
        }

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (detected_language, confidence_score)
            Returns ('unknown', 0.0) if detection fails
        """
        if not detect:
            print("WARNING: Language detection not available. Please install langdetect.")
            return 'unknown', 0.0

        if not text or not text.strip():
            return 'unknown', 0.0

        try:
            # Clean text for better detection
            clean_text = text.strip()

            # Detect language
            detected_lang = detect(clean_text)

            # Calculate confidence based on text length and common patterns
            confidence = self._calculate_confidence(clean_text, detected_lang)

            print(f"Detected language: {detected_lang} (confidence: {confidence:.2f})")

            return detected_lang, confidence

        except LangDetectError as e:
            print(f"Language detection failed: {e}")
            return 'unknown', 0.0
        except Exception as e:
            print(f"Unexpected error in language detection: {e}")
            return 'unknown', 0.0

    def _calculate_confidence(self, text: str, detected_lang: str) -> float:
        """
        Calculate confidence score for language detection
        
        Args:
            text: Original text
            detected_lang: Detected language code
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.7  # Base confidence for langdetect

        # Increase confidence for longer texts
        length_bonus = min(len(text) / 100, 0.2)

        # Check for language-specific patterns
        pattern_bonus = 0.0

        if detected_lang in ['zh', 'zh-cn', 'zh-tw']:
            # Check for Chinese characters (CJK range)
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            if chinese_chars > 0:
                pattern_bonus = min(chinese_chars / len(text), 0.1)

        elif detected_lang == 'en':
            # Check for common English patterns
            english_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that']
            text_lower = text.lower()
            english_word_count = sum(1 for word in english_words if word in text_lower)
            if english_word_count > 0:
                pattern_bonus = min(english_word_count / 10, 0.1)

        final_confidence = min(base_confidence + length_bonus + pattern_bonus, 1.0)
        return final_confidence

    def determine_translation_direction(self, text: str) -> Dict[str, any]:
        """
        Determine which translation direction to use based on detected language
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with translation info:
            {
                'source_language': str,
                'target_language': str, 
                'task_id': str,
                'prompt': str,
                'confidence': float,
                'auto_detected': bool
            }
        """
        detected_lang, confidence = self.detect_language(text)

        # Default fallback
        result = {
            'source_language': 'unknown',
            'target_language': 'unknown',
            'task_id': 'refine',  # Fallback to refine if can't determine
            'prompt': '',
            'confidence': confidence,
            'auto_detected': True,
            'detected_code': detected_lang
        }

        # Determine translation direction based on detected language
        if detected_lang in ['zh', 'zh-cn', 'zh-tw']:
            # Chinese detected -> translate to English
            result.update({
                'source_language': 'Chinese',
                'target_language': 'English',
                'task_id': 'zh_to_en',
                'prompt': TRANSLATE_ZH_TO_EN_PROMPT
            })
            print(f"Auto-translation: Chinese -> English")

        elif detected_lang == 'en':
            # English detected -> translate to Simplified Chinese
            result.update({
                'source_language': 'English',
                'target_language': 'Simplified Chinese',
                'task_id': 'en_to_zh',
                'prompt': TRANSLATE_EN_TO_ZH_PROMPT
            })
            print(f"Auto-translation: English -> Simplified Chinese")

        else:
            # Unknown language or unsupported
            print(f"Unknown or unsupported language: {detected_lang}")
            print(f"Falling back to text refinement instead of translation")
            result.update({
                'source_language': f'Unknown ({detected_lang})',
                'target_language': 'Refined Text',
                'task_id': 'refine',
                'auto_detected': False
            })

        return result

    def get_translation_summary(self, translation_info: Dict[str, any], text_preview: str = "") -> str:
        """
        Generate a summary of the translation that will be performed
        
        Args:
            translation_info: Translation info from determine_translation_direction
            text_preview: Preview of the input text (optional)
            
        Returns:
            Formatted summary string
        """
        if not translation_info['auto_detected']:
            return f"Language auto-detection failed. Using text refinement instead."

        confidence = translation_info['confidence']
        confidence_level = "High" if confidence > 0.8 else "Medium" if confidence > 0.6 else "Low"

        summary = f"""AUTO-TRANSLATION DETECTED
        
Language Detection: {translation_info['source_language']} (confidence: {confidence:.1%} - {confidence_level})
Translation Direction: {translation_info['source_language']} -> {translation_info['target_language']}
Task: {translation_info['task_id']}"""

        if text_preview and len(text_preview) > 50:
            preview = text_preview[:50] + "..."
            summary += f"\nText Preview: {preview}"

        return summary


def create_auto_translate_task_info() -> Dict[str, any]:
    """
    Create task info for the new auto-translate feature
    
    Returns:
        Task info dictionary for settings.py
    """
    return {
        "id": "auto_translate",
        "name": "Auto-Translate (Detect Language & Translate)"
    }


# Quick test function
def test_language_detection():
    """Test the language detection functionality"""
    handler = TranslationHandler()

    test_cases = [
        "Hello, how are you today?",
        "Hi, I recently canceled one policy from my account.",
        "This is a test of the emergency broadcast system."
    ]

    print("=== Testing Language Detection ===")
    for text in test_cases:
        print(f"\nText: {text}")
        translation_info = handler.determine_translation_direction(text)
        summary = handler.get_translation_summary(translation_info, text)
        print(summary)
        print("-" * 50)


if __name__ == "__main__":
    test_language_detection()
