---
description: Common commands for running the app and tests
---

```bash
# Run the application
python3 main.py

# Run all unit tests
python3 -m pytest tests/

# Run a single test file
python3 -m pytest tests/test_app_manager.py

# Run a single test
python3 -m pytest tests/test_app_manager.py::TestTaskProcessor::test_execute_task_success

# Integration scripts (require real API keys in .env)
python3 scripts/test_providers.py       # test all 5 AI provider connections
python3 scripts/test_auto_translation.py
python3 scripts/test_installation.py    # verify dependencies
```
