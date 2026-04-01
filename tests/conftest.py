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


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "api: mark test as requiring API access")


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    for item in items:
        if item.fspath.basename.startswith('test_'):
            item.add_marker(pytest.mark.unit)
