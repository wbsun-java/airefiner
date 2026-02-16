"""
Structured logging system for the AIRefiner project.
Replaces scattered print statements with proper logging.
"""

import logging
import sys
from typing import Optional


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
        import copy
        record = copy.copy(record)
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class SafeColoredFormatter(logging.Formatter):
    """Safe colored formatter for console output without Unicode characters."""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    # Safe ASCII alternatives for Unicode emojis
    EMOJI_REPLACEMENTS = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        'ℹ️': '[INFO]',
        '⏳': '[LOADING]',
        '🔎': '[FILTER]',
        '📋': '[CACHE]',
        '💾': '[SAVE]',
        '📊': '[STATS]',
        '🔄': '[RETRY]',
        '⚪': '[SKIP]',
        '🤖': '[AI]',
        '👋': '[BYE]',
        '🗑️': '[CLEAR]',
    }

    def format(self, record):
        # Work on a copy to avoid mutating the shared record
        import copy
        record = copy.copy(record)

        # Replace Unicode emojis with ASCII alternatives
        message = record.getMessage()
        for emoji, replacement in self.EMOJI_REPLACEMENTS.items():
            message = message.replace(emoji, replacement)

        record.msg = message
        record.args = ()

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
        import os
        
        # Clear any existing handlers
        self.logger.handlers.clear()

        # Set default level
        self.logger.setLevel(logging.INFO)

        # Console handler with encoding-safe output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Use safe formatter on Windows to avoid Unicode issues
        if os.name == 'nt':  # Windows
            # Use safe formatter without emojis
            formatter = SafeColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            # Use regular colored formatter with emojis on Unix systems
            formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )

        console_handler.setFormatter(formatter)

        # Add handler
        self.logger.addHandler(console_handler)

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
