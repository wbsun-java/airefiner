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

# Integration scripts (require real API keys in .env)
python3 scripts/test_providers.py       # test all 5 AI provider connections
python3 scripts/test_auto_translation.py
python3 scripts/test_installation.py    # verify dependencies
```

## Architecture

The application has a strict 4-layer separation:

```
main.py (AIRefinerApp)
  └── ui/console_interface.py      # All user I/O — no business logic
  └── core/app_manager.py          # ApplicationManager + TaskProcessor — no I/O
        └── models/model_loader.py # Orchestrates provider loading + caching
              └── models/*_provider.py  # One file per AI provider
```

**Startup flow:** `load_config()` → `app_manager.initialize()` → `model_loader.initialize_models()` → `get_model_definitions()` (fetches from all 5 providers in parallel via `ThreadPoolExecutor`) → main loop.

**Request flow:** UI collects text → `ApplicationManager.process_text()` → `TaskProcessor.execute_task()` → builds a LangChain chain (`ChatPromptTemplate | model | StrOutputParser`) → invoked through the model's `CircuitBreaker`.

## Key Design Patterns

**Provider registry pattern** (`models/model_loader.py`): `_PROVIDER_REGISTRY` maps provider names to `(module_path, class_name)` tuples. Providers are lazily imported via `importlib`. Adding a new provider means adding one entry here and a new `*_provider.py` file.

**Provider contract** (`models/base_model_provider.py`): Every provider implements `fetch_models()`, `get_fallback_models()`, `get_model_class()`, and `get_model_id_key()`. The `create_model_definition()` base method produces the standardized dict (`key`, `model_name`, `class`, `args`, `model_id_key`) consumed by `initialize_models()`.

**Model keys** follow the format `"{provider}/{display_name}"` (e.g. `"anthropic/Claude Sonnet 4"`). These are the keys used throughout `ApplicationManager._models`.

**Task IDs** are constants on `TaskConfiguration` in `config/constants.py`. Always use the constant (e.g. `TaskConfiguration.REFINE_PRESENTATION`), never raw strings — the prompt map in `TaskProcessor.execute_task()` uses these as dict keys.

**xAI is a custom LangChain wrapper**: Unlike other providers which use official LangChain integrations, `models/xai_provider.py` contains a hand-rolled `ChatXAI(BaseChatModel)` that wraps the gRPC-based `xai_sdk`. The client is lazily cached via Pydantic `PrivateAttr`.

**Model filtering** (`models/model_filter.py`): `is_text_model()` applies keyword blocklist from `ModelFiltering.NON_TEXT_KEYWORDS` and per-provider exclusions from `ModelFiltering.PROVIDER_EXCLUSIONS`. `deduplicate_models()` drops dated snapshot IDs (e.g. `gpt-4o-2024-11-20`) when a base ID (e.g. `gpt-4o`) exists.

**Circuit breaker** (`utils/error_handler.py`): Each model key gets its own `CircuitBreaker` instance in `TaskProcessor`. After 3 failures it opens for 60 seconds, raising `APIError` instead of calling the model.

## Configuration

API keys are loaded from `.env` via `python-dotenv`. Supported variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`. At least one must be set.

`config/config_manager.py` holds the `TASKS` dict (maps menu numbers `"1"–"3"` to task dicts) and `_API_KEY_ARG_NAMES` (maps provider names to LangChain constructor argument names). Both must stay in sync with `ModelProvider` enum in `config/constants.py`.

## Test Mocking Notes

Tests in `tests/test_app_manager.py` patch `langchain_core.prompts.ChatPromptTemplate` and `prompts.refine_prompts` at their source module paths (not at `core.app_manager.*`). This works because `execute_task()` uses deferred imports. Do not move those imports to module level — it breaks the patches.
