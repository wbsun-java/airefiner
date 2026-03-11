"""
Configuration constants and enums for the AIRefiner project.
"""

from enum import Enum
from typing import Dict, List


class ModelProvider(Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    XAI = "xai"


# Cache configuration
CACHE_DURATION_SECONDS = 3600  # 1 hour

# Input configuration
MULTILINE_TERMINATOR = "done!!!"
DEFAULT_TEMPERATURE = 0.7


class ModelFiltering:
    """Model filtering configuration."""

    NON_TEXT_KEYWORDS = [
        'image', 'vision', 'dalle', 'dall-e', 'clip', 'vit', 'img', 'visual', 'pic', 'photo',
        'sora', 'robot',
        'babbage', 'davinci',
        'audio', 'tts', 'whisper', 'speech', 'voice', 'sound', 'music', 'orpheus',
        'arabic', 'allam',
        'video', 'vid', 'motion', 'animation',
        'embed', 'embedding', 'similarity', 'vector', 'retrieval',
        'code', 'programming', 'dev', 'developer',
        'moderation', 'safety', 'content-filter', 'toxic',
        'fine-tune', 'finetune', 'training', 'custom',
        'reasoning', 'math', 'science', 'research',
        'guard', 'guardian', 'safety-model',
        'edit', 'davinci-edit', 'curie-edit',
        'realtime', 'real-time', 'search', 'transcribe', 'transcription'
    ]

    PROVIDER_EXCLUSIONS: Dict[str, List[str]] = {
        ModelProvider.OPENAI.value: ['davinci-edit', 'curie-edit', 'babbage-edit', 'ada-edit'],
        ModelProvider.GOOGLE.value: ['bison', 'gecko', 'otter', 'unicorn', 'computer-use'],
        ModelProvider.ANTHROPIC.value: [],
        ModelProvider.GROQ.value: ['whisper', 'distil-whisper'],
        ModelProvider.XAI.value: [],
    }


class TaskConfiguration:
    """Task configuration constants."""
    REFINE = "refine"
    TRANSLATE_EN_TO_ZH = "en_to_zh"
    TRANSLATE_ZH_TO_EN = "zh_to_en"
    AUTO_TRANSLATE = "auto_translate"


class LanguageSupport:
    """Language support configuration."""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh-cn': 'Simplified Chinese',
        'zh-tw': 'Traditional Chinese',
        'zh': 'Chinese'
    }

    LANGUAGE_MAPPING = {
        'en': 'english',
        'zh-cn': 'chinese',
        'zh-tw': 'chinese',
        'zh': 'chinese'
    }

    CHINESE_UNICODE_RANGE = (0x4e00, 0x9fff)

    COMMON_ENGLISH_WORDS = [
        'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that'
    ]

    # Language detection tuning (absorbed from LanguageDetection)
    BASE_CONFIDENCE = 0.7
    MAX_LENGTH_BONUS = 0.2
    MAX_PATTERN_BONUS = 0.1
    LENGTH_DIVISOR = 100


# Keep LanguageDetection as alias for backward compatibility during transition
LanguageDetection = LanguageSupport


class UIConfig:
    """User interface configuration."""
    MENU_SEPARATOR = "-" * 50

    SUCCESS_PREFIX = "✅"
    ERROR_PREFIX = "❌"
    WARNING_PREFIX = "⚠️"
    INFO_PREFIX = "ℹ️"
    LOADING_PREFIX = "⏳"
    SEARCH_PREFIX = "🔎"
    CACHE_PREFIX = "📋"
    SAVE_PREFIX = "💾"
    STATS_PREFIX = "📊"
