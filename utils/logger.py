"""
Structured logging system for the AIRefiner project.
Replaces scattered print statements with proper logging.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from config.constants import LoggingConfig


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class AIRefinerLogger:
    """Centralized logger for the AIRefiner application."""

    _instance: Optional['AIRefinerLogger'] = None
    _initialized = False

    def __new__(cls) -> 'AIRefinerLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger('airefiner')
        self._setup_logging()
        self._initialized = True

    def _setup_logging(self):
        """Setup logging configuration."""
        # Clear any existing handlers
        self.logger.handlers.clear()

        # Set default level
        self.logger.setLevel(logging.INFO)

        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Use colored formatter for console
        colored_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(colored_formatter)

        # File handler for persistent logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "airefiner.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        # Plain formatter for file output
        file_formatter = logging.Formatter(
            LoggingConfig.DEFAULT_FORMAT,
            datefmt=LoggingConfig.DATE_FORMAT
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def set_level(self, level: str):
        """Set logging level."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))

    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> AIRefinerLogger:
        """Get logger instance."""
        if not hasattr(self, '_logger'):
            self._logger = AIRefinerLogger()
        return self._logger


# Global logger instance
logger = AIRefinerLogger()


def get_logger() -> AIRefinerLogger:
    """Get the global logger instance."""
    return logger


def set_log_level(level: str):
    """Set global log level."""
    logger.set_level(level)


# Convenience functions for direct usage
def debug(message: str, *args, **kwargs):
    """Log debug message using global logger."""
    logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log info message using global logger."""
    logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log warning message using global logger."""
    logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log error message using global logger."""
    logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log critical message using global logger."""
    logger.critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """Log exception with traceback using global logger."""
    logger.exception(message, *args, **kwargs)
