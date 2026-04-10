"""
Pytest configuration and shared fixtures for AIRefiner tests.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_logger_state():
    """Automatically reset logger state between tests."""
    import logging
    logging.getLogger('airefiner').handlers.clear()
    logging.getLogger('airefiner').setLevel(logging.NOTSET)

    yield

    logging.getLogger('airefiner').handlers.clear()
