---
description: Key design patterns used in this codebase
---

**Provider registry pattern** (`models/model_loader.py`): `_PROVIDER_REGISTRY` maps provider names to `(module_path, class_name)` tuples. Providers are lazily imported via `importlib`. Adding a new provider means adding one entry here and a new `*_provider.py` file.

**Provider contract** (`models/base_model_provider.py`): Every provider implements `fetch_models()`, `get_fallback_models()`, and `build_callable(model_id, api_key) -> Callable[[str], str]`. The `create_model_definition()` base method produces the standardized dict (`key`, `model_name`, `provider`) consumed by `initialize_models()`.

**Model keys** follow the format `"{provider}/{display_name}"` (e.g. `"anthropic/Claude Sonnet 4"`). These are the keys used throughout `ApplicationManager._models`.

**Task IDs** are constants on `TaskConfiguration` in `config/constants.py`. Always use the constant (e.g. `TaskConfiguration.REFINE_PRESENTATION`), never raw strings — the prompt map in `TaskProcessor.execute_task()` uses these as dict keys.

**xAI uses the native `xai-sdk`**: `models/xai_provider.py` imports `Client` from `xai_sdk` and uses the chat builder pattern (`client.chat.create` → `chat.append(user(...))` → `chat.sample()`). Model listing still uses the `openai` client pointed at `https://api.x.ai/v1`.

**Model filtering** (`models/model_filter.py`): `is_text_model()` applies keyword blocklist from `ModelFiltering.NON_TEXT_KEYWORDS` and per-provider exclusions from `ModelFiltering.PROVIDER_EXCLUSIONS`. `deduplicate_models()` drops dated snapshot IDs (e.g. `gpt-4o-2024-11-20`) when a base ID (e.g. `gpt-4o`) exists.

**Circuit breaker** (`utils/error_handler.py`): Each model key gets its own `CircuitBreaker` instance in `TaskProcessor`. After 3 failures it opens for 60 seconds, raising `APIError` instead of calling the model.
