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
```

Live provider calls require real API keys in `.env` and are not part of the default unit suite.
