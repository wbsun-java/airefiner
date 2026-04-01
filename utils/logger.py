"""
Structured logging system for the AIRefiner project.
"""

import copy
import logging
import os
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored formatter with optional emoji-to-ASCII replacement on Windows."""

    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'

    EMOJI_REPLACEMENTS = {
        '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARN]', 'ℹ️': '[INFO]',
        '⏳': '[LOADING]', '🔎': '[FILTER]', '📋': '[CACHE]', '💾': '[SAVE]',
        '📊': '[STATS]', '🔄': '[RETRY]', '⚪': '[SKIP]', '🤖': '[AI]',
        '👋': '[BYE]', '🗑️': '[CLEAR]',
    }

    def __init__(self, fmt=None, datefmt=None, *, safe_mode: bool = False):
        super().__init__(fmt, datefmt)
        self._safe_mode = safe_mode

    def format(self, record):
        record = copy.copy(record)

        if self._safe_mode:
            message = record.getMessage()
            for emoji, replacement in self.EMOJI_REPLACEMENTS.items():
                message = message.replace(emoji, replacement)
            record.msg = message
            record.args = ()

        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def _setup_logger() -> logging.Logger:
    """Create and configure the application logger."""
    _logger = logging.getLogger('airefiner')
    _logger.handlers.clear()
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        safe_mode=(os.name == 'nt'),
    ))
    _logger.addHandler(handler)
    return _logger


# Global logger instance
_log = _setup_logger()


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> logging.Logger:
        return _log


# Convenience functions for direct usage
def info(message: str, *args, **kwargs):
    _log.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    _log.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    _log.error(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    _log.exception(message, *args, **kwargs)
