"""
Centralized configuration management with validation for AIRefiner.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from config.constants import ModelProvider, TaskConfiguration, InputConfig
from utils.logger import LoggerMixin


@dataclass
class APIConfiguration:
    """Configuration for API keys and related settings."""

    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None
    groq_key: Optional[str] = None
    xai_key: Optional[str] = None

    # Constructor argument names for each provider
    api_key_arg_names: Dict[str, str] = field(default_factory=lambda: {
        ModelProvider.OPENAI.value: "openai_api_key",
        ModelProvider.ANTHROPIC.value: "anthropic_api_key",
        ModelProvider.GOOGLE.value: "google_api_key",
        ModelProvider.GROQ.value: "groq_api_key",
        ModelProvider.XAI.value: "xai_api_key",
    })

    @classmethod
    def from_environment(cls) -> 'APIConfiguration':
        """
        Create configuration from environment variables.
        
        Returns:
            APIConfiguration instance with values from environment
        """
        return cls(
            openai_key=os.getenv('OPENAI_API_KEY'),
            anthropic_key=os.getenv('ANTHROPIC_API_KEY'),
            google_key=os.getenv('GOOGLE_API_KEY'),
            groq_key=os.getenv('GROQ_API_KEY'),
            xai_key=os.getenv('XAI_API_KEY'),
        )

    def get_api_keys(self) -> Dict[str, str]:
        """
        Get dictionary of provider -> API key mappings (excluding None values).
        
        Returns:
            Dictionary of available API keys
        """
        keys = {
            ModelProvider.OPENAI.value: self.openai_key,
            ModelProvider.ANTHROPIC.value: self.anthropic_key,
            ModelProvider.GOOGLE.value: self.google_key,
            ModelProvider.GROQ.value: self.groq_key,
            ModelProvider.XAI.value: self.xai_key,
        }
        return {k: v for k, v in keys.items() if v is not None}

    def validate(self) -> List[str]:
        """
        Validate the API configuration.
        
        Returns:
            List of validation error messages
        """
        errors = []

        available_keys = self.get_api_keys()
        if not available_keys:
            errors.append("At least one API key must be provided")

        # Check for malformed keys (basic validation)
        for provider, key in available_keys.items():
            if not key.strip():
                errors.append(f"{provider} API key is empty")
            elif len(key) < 10:  # Most API keys are longer than 10 characters
                errors.append(f"{provider} API key appears to be too short")

        return errors

    def get_available_providers(self) -> List[str]:
        """Get list of providers with valid API keys."""
        return list(self.get_api_keys().keys())


@dataclass
class ModelFilteringConfiguration:
    """Configuration for model filtering."""

    enable_strict_filtering: bool = True
    custom_exclude_keywords: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate filtering configuration."""
        errors = []

        # Validate custom keywords are strings
        for keyword in self.custom_exclude_keywords:
            if not isinstance(keyword, str):
                errors.append(f"Custom exclude keyword must be string, got {type(keyword)}")

        return errors


@dataclass
class TasksConfiguration:
    """Configuration for available tasks."""

    tasks: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "1": {"id": TaskConfiguration.REFINE, "name": "Refine Text (Email, Article, etc.)"},
        "2": {"id": "refine_presentation", "name": "Refine Presentation (Summarize Article)"},
        "3": {"id": TaskConfiguration.AUTO_TRANSLATE, "name": "Auto-Translate (Detect Language & Translate)"},
    })

    def validate(self) -> List[str]:
        """Validate task configuration."""
        errors = []

        if not self.tasks:
            errors.append("At least one task must be defined")

        for key, task in self.tasks.items():
            if not isinstance(task, dict):
                errors.append(f"Task {key} must be a dictionary")
                continue

            if "id" not in task:
                errors.append(f"Task {key} missing required 'id' field")

            if "name" not in task:
                errors.append(f"Task {key} missing required 'name' field")

            # Validate task ID is known
            valid_task_ids = [
                TaskConfiguration.REFINE,
                TaskConfiguration.TRANSLATE_EN_TO_ZH,
                TaskConfiguration.TRANSLATE_ZH_TO_EN,
                TaskConfiguration.AUTO_TRANSLATE,
                "refine_presentation"  # Legacy task ID
            ]

            if task.get("id") not in valid_task_ids:
                errors.append(f"Task {key} has unknown task ID: {task.get('id')}")

        return errors

    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task configuration by task ID."""
        for task in self.tasks.values():
            if task.get("id") == task_id:
                return task
        return None


@dataclass
class ApplicationConfiguration:
    """Main application configuration."""

    api_config: APIConfiguration
    model_filtering: ModelFilteringConfiguration = field(default_factory=ModelFilteringConfiguration)
    tasks_config: TasksConfiguration = field(default_factory=TasksConfiguration)
    default_temperature: float = InputConfig.DEFAULT_TEMPERATURE
    log_level: str = "INFO"

    def validate(self) -> List[str]:
        """
        Validate the entire configuration.
        
        Returns:
            List of all validation errors
        """
        errors = []

        # Validate sub-configurations
        errors.extend(self.api_config.validate())
        errors.extend(self.model_filtering.validate())
        errors.extend(self.tasks_config.validate())

        # Validate application-level settings
        if not (0.0 <= self.default_temperature <= 2.0):
            errors.append(f"Default temperature must be between 0.0 and 2.0, got {self.default_temperature}")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Log level must be one of {valid_log_levels}, got {self.log_level}")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0


class ConfigurationManager(LoggerMixin):
    """Manages application configuration with validation and environment loading."""

    def __init__(self):
        super().__init__()
        self._config: Optional[ApplicationConfiguration] = None

    def load_configuration(self, config_file: Optional[Path] = None) -> ApplicationConfiguration:
        """
        Load configuration from environment and optionally from file.
        
        Args:
            config_file: Optional path to configuration file (not implemented yet)
            
        Returns:
            Loaded and validated configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.logger.info("Loading application configuration...")

        # Load API configuration from environment
        api_config = APIConfiguration.from_environment()

        # Load other configurations (currently from defaults, could be extended to file-based)
        model_filtering = ModelFilteringConfiguration(
            enable_strict_filtering=True,
            custom_exclude_keywords=[]  # Could be loaded from file
        )

        tasks_config = TasksConfiguration()

        # Create main configuration
        config = ApplicationConfiguration(
            api_config=api_config,
            model_filtering=model_filtering,
            tasks_config=tasks_config,
            log_level=os.getenv('LOG_LEVEL', 'INFO').upper()
        )

        # Validate configuration
        errors = config.validate()
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self._config = config
        self.logger.info("Configuration loaded and validated successfully")
        self._log_configuration_summary(config)

        return config

    def get_configuration(self) -> ApplicationConfiguration:
        """
        Get the current configuration.
        
        Returns:
            Current configuration
            
        Raises:
            RuntimeError: If configuration not loaded yet
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_configuration() first.")
        return self._config

    def _log_configuration_summary(self, config: ApplicationConfiguration):
        """Log a summary of the loaded configuration."""
        available_providers = config.api_config.get_available_providers()
        self.logger.info(
            f"Available API providers: {', '.join(available_providers) if available_providers else 'None'}")
        self.logger.info(f"Model filtering enabled: {config.model_filtering.enable_strict_filtering}")
        self.logger.info(f"Number of tasks configured: {len(config.tasks_config.tasks)}")
        self.logger.info(f"Default temperature: {config.default_temperature}")
        self.logger.info(f"Log level: {config.log_level}")

        if not available_providers:
            self.logger.warning("No API keys found - application may not function properly")


# Global configuration manager instance
_config_manager = ConfigurationManager()


def load_config(config_file: Optional[Path] = None) -> ApplicationConfiguration:
    """
    Load application configuration.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Loaded configuration
    """
    return _config_manager.load_configuration(config_file)


def get_config() -> ApplicationConfiguration:
    """
    Get the current application configuration.
    
    Returns:
        Current configuration
    """
    return _config_manager.get_configuration()
