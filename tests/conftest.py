"""
Pytest configuration and shared fixtures for AIRefiner tests.
"""

# Add the project root to sys.path for imports
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables."""
    return {
        'OPENAI_API_KEY': 'sk-test-openai-key-1234567890',
        'ANTHROPIC_API_KEY': 'sk-ant-test-key-1234567890',
        'GOOGLE_API_KEY': 'test-google-key-1234567890',
        'GROQ_API_KEY': 'gsk-test-groq-key-1234567890',
        'XAI_API_KEY': 'xai-test-key-1234567890',
        'LOG_LEVEL': 'INFO'
    }


@pytest.fixture
def clean_environment():
    """Fixture to provide clean environment (no API keys)."""
    return {}


@pytest.fixture
def mock_model_instance():
    """Fixture to provide a mock model instance."""
    mock_model = Mock()
    mock_model.invoke.return_value = "Mock response"
    return mock_model


@pytest.fixture
def mock_api_configuration():
    """Fixture to provide a mock API configuration."""
    from config.config_manager import APIConfiguration

    return APIConfiguration(
        openai_key='sk-test-openai-key-1234567890',
        anthropic_key='sk-ant-test-key-1234567890',
        google_key='test-google-key-1234567890'
    )


@pytest.fixture
def mock_task_configuration():
    """Fixture to provide a mock tasks configuration."""
    from config.config_manager import TasksConfiguration

    return TasksConfiguration(tasks={
        "1": {"id": "refine", "name": "Refine Text"},
        "2": {"id": "auto_translate", "name": "Auto-Translate"}
    })


@pytest.fixture
def mock_application_config(mock_api_configuration, mock_task_configuration):
    """Fixture to provide a complete mock application configuration."""
    from config.config_manager import ApplicationConfiguration, ModelFilteringConfiguration

    return ApplicationConfiguration(
        api_config=mock_api_configuration,
        model_filtering=ModelFilteringConfiguration(),
        tasks_config=mock_task_configuration
    )


@pytest.fixture(autouse=True)
def reset_logger_state():
    """Automatically reset logger state between tests."""
    # Clear any existing loggers
    import logging
    logging.getLogger('airefiner').handlers.clear()
    logging.getLogger('airefiner').setLevel(logging.NOTSET)

    yield

    # Clean up after test
    logging.getLogger('airefiner').handlers.clear()


@pytest.fixture
def mock_langchain_imports():
    """Mock LangChain imports to avoid import issues in tests."""
    with patch.dict('sys.modules', {
        'langchain_core.prompts': Mock(),
        'langchain_core.output_parsers': Mock(),
        'langchain_openai': Mock(),
        'langchain_anthropic': Mock(),
        'langchain_google_genai': Mock(),
        'langchain_groq': Mock(),
        'langchain_xai': Mock(),
    }):
        yield


@pytest.fixture
def suppress_logging():
    """Fixture to suppress logging output during tests."""
    import logging

    # Set logging level to CRITICAL to suppress most output
    old_level = logging.getLogger().level
    logging.getLogger().setLevel(logging.CRITICAL)

    yield

    # Restore original level
    logging.getLogger().setLevel(old_level)


@pytest.fixture
def temp_config_file(tmp_path):
    """Fixture to provide a temporary configuration file."""
    config_file = tmp_path / "test_config.json"
    config_content = {
        "api_keys": {
            "openai": "sk-test-key",
            "anthropic": "sk-ant-test"
        },
        "model_filtering": {
            "enable_strict_filtering": True,
            "custom_exclude_keywords": ["test", "debug"]
        },
        "default_temperature": 0.7,
        "log_level": "INFO"
    }

    import json
    config_file.write_text(json.dumps(config_content, indent=2))
    return config_file


class MockResponse:
    """Mock HTTP response for testing API calls."""

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_successful_api_response():
    """Fixture for successful API response."""
    return MockResponse({
        "data": [
            {"id": "gpt-4", "object": "model"},
            {"id": "gpt-3.5-turbo", "object": "model"}
        ]
    })


@pytest.fixture
def mock_failed_api_response():
    """Fixture for failed API response."""
    return MockResponse({"error": "Unauthorized"}, 401)


# Custom pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring API access"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    # Add 'unit' marker to all tests in test files starting with 'test_'
    for item in items:
        if item.fspath.basename.startswith('test_'):
            item.add_marker(pytest.mark.unit)
