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


class CacheConfig:
    """Cache configuration constants."""
    DURATION_SECONDS = 3600  # 1 hour
    CACHE_DURATION_MINUTES = DURATION_SECONDS // 60


class InputConfig:
    """Input handling configuration."""
    MULTILINE_TERMINATOR = "done!!!"
    DEFAULT_TEMPERATURE = 0.7


class ConfidenceThresholds:
    """Confidence threshold constants for language detection."""
    HIGH = 0.8
    MEDIUM = 0.6


class LanguageDetection:
    """Language detection configuration."""
    BASE_CONFIDENCE = 0.7
    MAX_LENGTH_BONUS = 0.2
    MAX_PATTERN_BONUS = 0.1
    LENGTH_DIVISOR = 100


class ModelFiltering:
    """Model filtering configuration."""

    # Common non-text keywords across all providers
    NON_TEXT_KEYWORDS = [
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
        'edit', 'davinci-edit', 'curie-edit',
        # Specialized/Real-time models (not suitable for text refinement)
        'realtime', 'real-time', 'search', 'transcribe', 'transcription'
    ]

    # Provider-specific exclusions
    PROVIDER_EXCLUSIONS: Dict[str, List[str]] = {
        ModelProvider.OPENAI.value: ['davinci-edit', 'curie-edit', 'babbage-edit', 'ada-edit'],
        ModelProvider.GOOGLE.value: ['bison', 'gecko', 'otter', 'unicorn', 'computer-use'],  # Legacy/specialized Gemini models
        ModelProvider.ANTHROPIC.value: [],  # Claude models are generally text-focused
        ModelProvider.GROQ.value: ['whisper', 'distil-whisper'],  # Audio transcription models
        ModelProvider.XAI.value: [],  # Grok models are generally text-focused
    }

    # Text model indicators
    TEXT_INDICATORS = [
        'chat', 'gpt', 'o1', 'claude', 'gemini', 'llama', 'mistral', 'mixtral', 'deepseek', 'grok',
        'gemma', 'kimi',
        'text', 'language', 'conversation', 'instruct', 'assistant'
    ]


class TaskConfiguration:
    """Task configuration constants."""

    # Task types
    REFINE = "refine"
    TRANSLATE_EN_TO_ZH = "en_to_zh"
    TRANSLATE_ZH_TO_EN = "zh_to_en"
    AUTO_TRANSLATE = "auto_translate"

    # Task names for display
    TASK_NAMES = {
        REFINE: "Refine Text",
        TRANSLATE_EN_TO_ZH: "English to Chinese",
        TRANSLATE_ZH_TO_EN: "Chinese to English",
        AUTO_TRANSLATE: "Auto-Translate (Detect Language & Translate)"
    }


class LanguageSupport:
    """Language support configuration."""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh-cn': 'Simplified Chinese',
        'zh-tw': 'Traditional Chinese',
        'zh': 'Chinese'  # Generic Chinese
    }

    LANGUAGE_MAPPING = {
        'en': 'english',
        'zh-cn': 'chinese',
        'zh-tw': 'chinese',
        'zh': 'chinese'
    }

    # Unicode ranges
    CHINESE_UNICODE_RANGE = (0x4e00, 0x9fff)  # CJK Unified Ideographs

    # Common English words for pattern detection
    COMMON_ENGLISH_WORDS = [
        'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that'
    ]


class UIConfig:
    """User interface configuration."""

    # Menu display
    MENU_SEPARATOR = "-" * 50
    MENU_WIDTH = 80

    # Status messages
    SUCCESS_PREFIX = "✅"
    ERROR_PREFIX = "❌"
    WARNING_PREFIX = "⚠️"
    INFO_PREFIX = "ℹ️"
    LOADING_PREFIX = "⏳"
    SEARCH_PREFIX = "🔎"
    CACHE_PREFIX = "📋"
    SAVE_PREFIX = "💾"
    STATS_PREFIX = "📊"

    # Colors (for terminal output)
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
