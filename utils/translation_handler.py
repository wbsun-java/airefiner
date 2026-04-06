"""
Translation Handler - Automatic language detection and translation.
"""

from typing import Dict, Any

try:
    from langdetect import detect
    from langdetect.lang_detect_exception import LangDetectException

    LangDetectError = LangDetectException
except ImportError:
    detect = None
    LangDetectError = Exception

from prompts.translate_prompts import TRANSLATE_EN_TO_ZH_PROMPT, TRANSLATE_ZH_TO_EN_PROMPT
from prompts.refine_prompts import REFINE_TEXT_PROMPT
from config.constants import LanguageSupport, TaskConfiguration
from utils.logger import LoggerMixin


class TranslationHandler(LoggerMixin):
    """Handles automatic language detection and translation between English and Chinese."""

    def detect_language(self, text: str) -> tuple:
        if not detect or not text.strip():
            return 'unknown', 0.0

        try:
            clean_text = text.strip()
            detected_lang = detect(clean_text)
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
        base_confidence = LanguageSupport.BASE_CONFIDENCE
        length_bonus = min(len(text) / LanguageSupport.LENGTH_DIVISOR, LanguageSupport.MAX_LENGTH_BONUS)
        pattern_bonus = 0.0

        if detected_lang in ['zh', 'zh-cn', 'zh-tw']:
            chinese_range = LanguageSupport.CHINESE_UNICODE_RANGE
            chinese_chars = sum(1 for c in text if chinese_range[0] <= ord(c) <= chinese_range[1])
            pattern_bonus = min(chinese_chars / len(text), LanguageSupport.MAX_PATTERN_BONUS)
        elif detected_lang == 'en':
            text_words = set(text.lower().split())
            english_words = set(LanguageSupport.COMMON_ENGLISH_WORDS)
            match_count = len(text_words.intersection(english_words))
            pattern_bonus = min(match_count / 10, LanguageSupport.MAX_PATTERN_BONUS)

        return min(base_confidence + length_bonus + pattern_bonus, 1.0)

    def determine_translation_direction(self, text: str) -> Dict[str, Any]:
        detected_lang, confidence = self.detect_language(text)

        if detected_lang in ['zh', 'zh-cn', 'zh-tw']:
            self.logger.info("Auto-translation: Chinese -> English")
            return {
                'source_language': 'Chinese',
                'target_language': 'English',
                'task_id': TaskConfiguration.TRANSLATE_ZH_TO_EN,
                'prompt': TRANSLATE_ZH_TO_EN_PROMPT,
            }
        elif detected_lang == 'en':
            self.logger.info("Auto-translation: English -> Simplified Chinese")
            return {
                'source_language': 'English',
                'target_language': 'Simplified Chinese',
                'task_id': TaskConfiguration.TRANSLATE_EN_TO_ZH,
                'prompt': TRANSLATE_EN_TO_ZH_PROMPT,
            }
        else:
            self.logger.warning(f"Unsupported language '{detected_lang}', falling back to text refinement")
            return {
                'source_language': f'Unknown ({detected_lang})',
                'target_language': 'Refined Text',
                'task_id': TaskConfiguration.REFINE,
                'prompt': REFINE_TEXT_PROMPT,
            }

    def get_translation_prompt(self, text: str) -> str:
        info = self.determine_translation_direction(text)
        self.logger.info(f"Translation: {info['source_language']} -> {info['target_language']}, task: {info['task_id']}")
        return info['prompt']
