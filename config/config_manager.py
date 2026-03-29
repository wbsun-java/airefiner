"""
Centralized configuration management with validation for AIRefiner.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from config.constants import ModelProvider, TaskConfiguration, DEFAULT_TEMPERATURE
from utils.logger import info, warning, error as log_error


# Hardcoded tasks - these don't change at runtime
TASKS: Dict[str, Dict[str, Any]] = {
    "1": {"id": TaskConfiguration.REFINE, "name": "Refine Text (Email, Article, etc.)"},
    "2": {"id": TaskConfiguration.REFINE_PRESENTATION, "name": "Refine Presentation (Summarize Article)"},
    "3": {"id": TaskConfiguration.AUTO_TRANSLATE, "name": "Auto-Translate (Detect Language & Translate)"},
}


@dataclass
class APIConfiguration:
    """Configuration for API keys and related settings."""

    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    groq_key: Optional[str] = None
    xai_key: Optional[str] = None

    @classmethod
    def from_environment(cls) -> 'APIConfiguration':
        return cls(
            openai_key=os.getenv('OPENAI_API_KEY'),
            anthropic_key=os.getenv('ANTHROPIC_API_KEY'),
            google_key=os.getenv('GOOGLE_API_KEY'),
            groq_key=os.getenv('GROQ_API_KEY'),
            xai_key=os.getenv('XAI_API_KEY'),
        )

    def get_api_keys(self) -> Dict[str, str]:
        keys = {
            ModelProvider.OPENAI.value: self.openai_key,
            ModelProvider.ANTHROPIC.value: self.anthropic_key,
            ModelProvider.GOOGLE.value: self.google_key,
            ModelProvider.GROQ.value: self.groq_key,
            ModelProvider.XAI.value: self.xai_key,
        }
        return {k: v for k, v in keys.items() if v is not None}

    def validate(self) -> List[str]:
        errors = []
        available_keys = self.get_api_keys()
        if not available_keys:
            errors.append("At least one API key must be provided")

        for provider, key in available_keys.items():
            if not key.strip():
                errors.append(f"{provider} API key is empty")
            elif len(key) < 10:
                errors.append(f"{provider} API key appears to be too short")

        return errors

    def get_available_providers(self) -> List[str]:
        return list(self.get_api_keys().keys())


@dataclass
class ApplicationConfiguration:
    """Main application configuration."""

    api_config: APIConfiguration
    default_temperature: float = DEFAULT_TEMPERATURE

    @property
    def tasks(self) -> Dict[str, Dict[str, Any]]:
        return TASKS

    def validate(self) -> List[str]:
        errors = []
        errors.extend(self.api_config.validate())

        if not (0.0 <= self.default_temperature <= 2.0):
            errors.append(f"Default temperature must be between 0.0 and 2.0, got {self.default_temperature}")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


# Module-level config state
_config: Optional[ApplicationConfiguration] = None


def load_config() -> ApplicationConfiguration:
    global _config
    info("Loading application configuration...")

    api_config = APIConfiguration.from_environment()
    config = ApplicationConfiguration(api_config=api_config)

    errors = config.validate()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        log_error(error_msg)
        raise ValueError(error_msg)

    _config = config
    info("Configuration loaded and validated successfully")

    available_providers = config.api_config.get_available_providers()
    info(f"Available API providers: {', '.join(available_providers) if available_providers else 'None'}")
    info(f"Default temperature: {config.default_temperature}")

    if not available_providers:
        warning("No API keys found - application may not function properly")

    return config


def get_config() -> ApplicationConfiguration:
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config
