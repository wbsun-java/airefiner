# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

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

## Architecture

The application has a strict 4-layer separation:

```
main.py (AIRefinerApp)
  └── ui/console_interface.py      # All user I/O — no business logic
  └── core/app_manager.py          # ApplicationManager + TaskProcessor — no I/O
        └── models/model_loader.py # Orchestrates provider loading + caching
              └── models/*_provider.py  # One file per AI provider
```

**Startup flow:** `load_config()` → `app_manager.initialize()` → `model_loader.initialize_models()` → `get_model_definitions()` (fetches from all 4 providers in parallel via `ThreadPoolExecutor`) → main loop.

**Request flow:** UI collects text → `ApplicationManager.process_text()` → `TaskProcessor.execute_task()` → formats the task prompt with `{user_text}` → invokes the model `Callable[[str], str]` through the model's `CircuitBreaker`.

## Key Design Patterns

**Provider registry pattern** (`models/model_loader.py`): `_PROVIDER_REGISTRY` maps provider names to `(module_path, class_name)` tuples. Providers are lazily imported via `importlib`. Adding a new provider means adding one entry here and a new `*_provider.py` file.

**Provider contract** (`models/base_model_provider.py`): Every provider implements `fetch_models()`, `get_fallback_models()`, and `build_callable(model_id, api_key) -> Callable[[str], str]`. The `create_model_definition()` base method produces the standardized dict (`key`, `model_name`, `provider`) consumed by `initialize_models()`.

**Model keys** follow the format `"{provider}/{display_name}"` (e.g. `"anthropic/Claude Sonnet 4"`). These are the keys used throughout `ApplicationManager._models`.

**Task IDs** are constants on `TaskConfiguration` in `config/constants.py`. Always use the constant (e.g. `TaskConfiguration.REFINE_PRESENTATION`), never raw strings — the prompt map in `TaskProcessor.execute_task()` uses these as dict keys.

**xAI uses the native `xai-sdk`**: `models/xai_provider.py` uses `client.models.list_language_models()` for model listing and the chat builder pattern (`client.chat.create` → `chat.append(user(...))` → `chat.sample()`) for inference.

**Model filtering** (`models/model_filter.py`): `is_text_model()` applies keyword blocklist from `ModelFiltering.NON_TEXT_KEYWORDS` and per-provider exclusions from `ModelFiltering.PROVIDER_EXCLUSIONS`. `deduplicate_models()` drops dated snapshot IDs (e.g. `gpt-4o-2024-11-20`) when a base ID (e.g. `gpt-4o`) exists.

**Circuit breaker** (`utils/error_handler.py`): Each model key gets its own `CircuitBreaker` instance in `TaskProcessor`. After 3 failures it opens for 60 seconds, raising `APIError` instead of calling the model.

## Configuration

API keys are loaded from `.env` via `python-dotenv`. Supported variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`. At least one must be set.

`config/config_manager.py` holds the `TASKS` dict (maps menu numbers `"1"–"3"` to task dicts). This must stay in sync with `TaskConfiguration` constants in `config/constants.py`.

## Test Mocking Notes

Tests in `tests/test_app_manager.py` patch `prompts.refine_prompts` at its source module path (not at `core.app_manager.*`). This works because `execute_task()` uses a deferred import. Do not move that import to module level — it breaks the patches.

Model objects in `_models` are `Callable[[str], str]`. In tests, use `Mock(return_value="some text")` as the model — the mock is called with the fully-formatted prompt string.
