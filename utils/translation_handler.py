#!/usr/bin/env python3
"""
Translation Handler - Automatic language detection and translation
"""

import os
import sys
from typing import Dict, Tuple, Any

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
from prompts.refine_prompts import REFINE_TEXT_PROMPT
from config.constants import LanguageSupport, LanguageDetection, ConfidenceThresholds
from utils.logger import LoggerMixin, info


class TranslationHandler(LoggerMixin):
    """
    Handles automatic language detection and translation between English and Chinese
    """

    def __init__(self):
        """Initialize the translation handler"""
        self.supported_languages = LanguageSupport.SUPPORTED_LANGUAGES
        self.language_mapping = LanguageSupport.LANGUAGE_MAPPING

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text using the langdetect library.
        
        This method analyzes the input text to determine its language and calculates
        a confidence score based on text length and language-specific patterns.
        Falls back gracefully if language detection is not available.
        
        Args:
            text: Input text to analyze for language detection
            
        Returns:
            Tuple[str, float]: A tuple containing:
                - detected_language: Language code (e.g., 'en', 'zh', 'zh-cn') or 'unknown'
                - confidence_score: Float between 0.0 and 1.0 indicating detection confidence
                
        Example:
            >>> handler = TranslationHandler()
            >>> lang, conf = handler.detect_language("Hello world")
            >>> lang
            'en'
            >>> conf > 0.5
            True
        """
        if not detect:
            self.logger.warning("Language detection not available. Please install langdetect.")
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

            self.logger.info(f"Detected language: {detected_lang} (confidence: {confidence:.2f})")

            return detected_lang, confidence

        except LangDetectError as e:
            self.logger.warning(f"Language detection failed: {e}")
            return 'unknown', 0.0
        except Exception as e:
            self.logger.error(f"Unexpected error in language detection: {e}")
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
        base_confidence = LanguageDetection.BASE_CONFIDENCE

        # Increase confidence for longer texts
        length_bonus = min(len(text) / LanguageDetection.LENGTH_DIVISOR, LanguageDetection.MAX_LENGTH_BONUS)

        # Check for language-specific patterns
        pattern_bonus = 0.0

        if detected_lang in ['zh', 'zh-cn', 'zh-tw']:
            # Check for Chinese characters (CJK range)
            chinese_range = LanguageSupport.CHINESE_UNICODE_RANGE
            chinese_chars = sum(1 for char in text if chinese_range[0] <= ord(char) <= chinese_range[1])
            if chinese_chars > 0:
                pattern_bonus = min(chinese_chars / len(text), LanguageDetection.MAX_PATTERN_BONUS)

        elif detected_lang == 'en':
            # Check for common English patterns
            # For efficiency, COMMON_ENGLISH_WORDS in LanguageSupport should be a set of lowercase words.
            common_english_words_set = set(LanguageSupport.COMMON_ENGLISH_WORDS)

            # Tokenize text into words to avoid partial matches (e.g., 'the' in 'there').
            # This is a simple tokenizer; a more robust one could use regex.
            text_words = set(text.lower().split())

            english_word_count = len(text_words.intersection(common_english_words_set))
            if english_word_count > 0:
                pattern_bonus = min(english_word_count / 10, LanguageDetection.MAX_PATTERN_BONUS)

        final_confidence = min(base_confidence + length_bonus + pattern_bonus, 1.0)
        return final_confidence

    def determine_translation_direction(self, text: str) -> Dict[str, Any]:
        """
        Determine which translation direction to use based on detected language.
        
        This method analyzes the input text to detect its language and determines
        the appropriate translation direction (e.g., Chinese to English or vice versa).
        If the language cannot be determined or is unsupported, it falls back to
        text refinement instead of translation.
        
        Args:
            text: Input text to analyze for translation direction
            
        Returns:
            Dict[str, Any]: Dictionary containing translation configuration:
                - source_language (str): Detected source language name
                - target_language (str): Target language for translation
                - task_id (str): Task identifier ('zh_to_en', 'en_to_zh', or 'refine')
                - prompt (str): Translation prompt template
                - confidence (float): Language detection confidence (0.0-1.0)
                - auto_detected (bool): Whether language was successfully auto-detected
                - detected_code (str): Raw language code from detection
                
        Example:
            >>> handler = TranslationHandler()
            >>> result = handler.determine_translation_direction("Hello world")
            >>> result['task_id']
            'en_to_zh'
            >>> result['source_language']
            'English'
        """
        detected_lang, confidence = self.detect_language(text)

        # Default fallback
        result = {
            'source_language': 'unknown',
            'target_language': 'unknown',
            'task_id': 'refine',  # Fallback to refine if can't determine
            'prompt': REFINE_TEXT_PROMPT,
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
            self.logger.info(f"Auto-translation: Chinese -> English")

        elif detected_lang == 'en':
            # English detected -> translate to Simplified Chinese
            result.update({
                'source_language': 'English',
                'target_language': 'Simplified Chinese',
                'task_id': 'en_to_zh',
                'prompt': TRANSLATE_EN_TO_ZH_PROMPT
            })
            self.logger.info(f"Auto-translation: English -> Simplified Chinese")

        else:
            # Unknown language or unsupported
            self.logger.warning(f"Unknown or unsupported language: {detected_lang}")
            self.logger.info(f"Falling back to text refinement instead of translation")
            result.update({
                'source_language': f'Unknown ({detected_lang})',
                'target_language': 'Refined Text',
                'auto_detected': False
            })

        return result

    def get_translation_prompt(self, text: str) -> str:
        """
        Determine the translation direction and return the appropriate prompt template.
        
        This method serves as the main entry point for auto-translation. It detects
        the language of the input text, determines the translation direction, and
        returns the appropriate prompt template. It also logs a summary of the
        translation operation for user visibility.
        
        Args:
            text: Input text to be translated
            
        Returns:
            str: Prompt template string for the detected translation task
                 Falls back to refinement prompt if translation is not applicable
                 
        Example:
            >>> handler = TranslationHandler()
            >>> prompt = handler.get_translation_prompt("Hello world")
            >>> "English" in prompt and "Chinese" in prompt
            True
        """
        translation_info = self.determine_translation_direction(text)

        # Show translation summary to the user
        summary = self.get_translation_summary(translation_info, text)
        self.logger.info(f"\n{summary}")

        self.logger.info(f"Using task: {translation_info['task_id']}")

        return translation_info['prompt']

    def get_translation_summary(self, translation_info: Dict[str, Any], text_preview: str = "") -> str:
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
        confidence_level = ("High" if confidence > ConfidenceThresholds.HIGH
                            else "Medium" if confidence > ConfidenceThresholds.MEDIUM
        else "Low")

        summary = f"""AUTO-TRANSLATION DETECTED

        Language Detection: {translation_info['source_language']} (confidence: {confidence:.1%} - {confidence_level})
        Translation Direction: {translation_info['source_language']} -> {translation_info['target_language']}
        Task: {translation_info['task_id']}"""

        if text_preview and len(text_preview) > 50:
            preview = text_preview[:50] + "..."
            summary += f"\nText Preview: {preview}"

        return summary


def create_auto_translate_task_info() -> Dict[str, Any]:
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

    info("=== Testing Language Detection ===")
    for text in test_cases:
        info(f"\nText: {text}")
        translation_info = handler.determine_translation_direction(text)
        summary = handler.get_translation_summary(translation_info, text)
        info(summary)
        info("-" * 50)


if __name__ == "__main__":
    test_language_detection()