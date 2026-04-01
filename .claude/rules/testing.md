---
description: Test mocking conventions and rules
---

Tests in `tests/test_app_manager.py` patch `prompts.refine_prompts` at its source module path (not at `core.app_manager.*`). This works because `execute_task()` uses a deferred import. Do not move those imports to module level — it breaks the patches.

Model objects in `_models` are `Callable[[str], str]`. In tests, use `Mock(return_value="some text")` as the model — the mock is called with the fully-formatted prompt string.
