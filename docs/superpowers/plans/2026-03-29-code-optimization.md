# Code Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate cross-provider duplication, streamline the model-loader startup path, tighten exception handling, and close test-coverage gaps.

**Architecture:** `BaseModelProvider` absorbs the try/except/fallback shell (`fetch_models`) and a shared list-builder (`_build_fallback_list`). Each provider implements only `_do_fetch_models`. `initialize_models` reads the API key that is already stored in each provider object instead of calling `get_config()` a second time. `process_text` splits its single merged `except` clause into two, matching the pattern already used by `TaskProcessor`.

**Tech Stack:** Python 3.14, pytest, `unittest.mock`. No new dependencies.

---

## File Map

| File | Change |
|---|---|
| `models/base_model_provider.py` | Add concrete `fetch_models()` (calls `_do_fetch_models()`), abstract `_do_fetch_models()`, and `_build_fallback_list()` helper |
| `models/anthropic_provider.py` | Rename `fetch_models` → `_do_fetch_models`; remove inner try/except |
| `models/openai_provider.py` | Same; simplify `get_fallback_models` to use `_build_fallback_list` |
| `models/google_provider.py` | Same |
| `models/groq_provider.py` | Same |
| `models/xai_provider.py` | Same |
| `models/model_loader.py` | Remove second `get_config()` call; read `api_key` from `provider.api_key` |
| `core/app_manager.py` | Split merged `except` in `process_text` into two clauses |
| `tests/test_base_model_provider.py` | New file — unit tests for base class helpers |
| `tests/test_app_manager.py` | Add circuit breaker integration tests and prompt-formatting edge-case test |

---

## Task 1: Add `fetch_models` template and `_build_fallback_list` to `BaseModelProvider`

**Files:**
- Create: `tests/test_base_model_provider.py`
- Modify: `models/base_model_provider.py`

### Step 1: Write the failing tests

Create `tests/test_base_model_provider.py`:

```python
"""
Unit tests for BaseModelProvider shared helpers.
"""
from unittest.mock import patch, Mock
import pytest
from models.base_model_provider import BaseModelProvider


class ConcreteProvider(BaseModelProvider):
    """Minimal concrete provider for testing the base class."""

    def _do_fetch_models(self):
        return [{"key": "p/m", "model_name": "m", "provider": self}]

    def get_fallback_models(self):
        return [{"key": "p/fallback", "model_name": "fallback", "provider": self}]

    def build_callable(self, model_id, api_key):
        return lambda prompt: "response"


@pytest.fixture
def provider():
    return ConcreteProvider(api_key="test-key", provider_name="testprovider")


class TestFetchModelsTemplate:
    def test_returns_do_fetch_result_on_success(self, provider):
        result = provider.fetch_models()
        assert result == [{"key": "p/m", "model_name": "m", "provider": provider}]

    def test_falls_back_on_exception(self, provider):
        with patch.object(provider, '_do_fetch_models', side_effect=RuntimeError("API down")):
            result = provider.fetch_models()
        assert result == [{"key": "p/fallback", "model_name": "fallback", "provider": provider}]

    def test_logs_error_on_exception(self, provider):
        with patch('models.base_model_provider.error') as mock_error, \
             patch.object(provider, '_do_fetch_models', side_effect=RuntimeError("API down")):
            provider.fetch_models()
        mock_error.assert_called_once()
        assert "testprovider" in mock_error.call_args[0][0]


class TestBuildFallbackList:
    def test_returns_definitions_for_valid_ids(self, provider):
        with patch('models.base_model_provider.is_text_model', return_value=True):
            result = provider._build_fallback_list(["model-a", "model-b"])
        assert len(result) == 2
        assert result[0]["model_name"] == "model-a"
        assert result[1]["model_name"] == "model-b"

    def test_filters_non_text_models(self, provider):
        def fake_is_text(model_id, provider_name):
            return model_id != "model-b"

        with patch('models.base_model_provider.is_text_model', side_effect=fake_is_text):
            result = provider._build_fallback_list(["model-a", "model-b"])
        assert len(result) == 1
        assert result[0]["model_name"] == "model-a"

    def test_uses_provider_name_for_filtering(self, provider):
        captured = []

        def capture_call(model_id, provider_name):
            captured.append(provider_name)
            return True

        with patch('models.base_model_provider.is_text_model', side_effect=capture_call):
            provider._build_fallback_list(["m"])
        assert captured == ["testprovider"]
```

- [ ] **Step 2: Run the tests — expect failures**

```bash
.venv/bin/python -m pytest tests/test_base_model_provider.py -v
```

Expected: all 6 tests FAIL with `AttributeError: '_do_fetch_models'` and `AttributeError: '_build_fallback_list'`.

- [ ] **Step 3: Implement the base class changes**

Replace the entire content of `models/base_model_provider.py` with:

```python
"""
Base classes for model providers to eliminate code duplication.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

from config.constants import DEFAULT_TEMPERATURE
from models.model_filter import is_text_model
from utils.logger import info, error, LoggerMixin


class BaseModelProvider(ABC, LoggerMixin):
    """
    Base class for all model providers.
    """

    def __init__(self, api_key: str, provider_name: str):
        self.api_key = api_key
        self.provider_name = provider_name
        self.default_temperature = DEFAULT_TEMPERATURE

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch models, falling back to get_fallback_models() on any error."""
        try:
            return self._do_fetch_models()
        except Exception as e:
            error(f"Failed to fetch {self.provider_name} models: {e}")
            info(f"Falling back to predefined {self.provider_name} models")
            return self.get_fallback_models()

    @abstractmethod
    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        pass

    def _build_fallback_list(self, model_ids: List[str]) -> List[Dict[str, Any]]:
        """Build model definitions from a list of IDs, filtering non-text models."""
        return [
            self.create_model_definition(m)
            for m in model_ids
            if is_text_model(m, self.provider_name)
        ]

    def create_model_definition(
        self, model_id: str, display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        if display_name is None:
            display_name = model_id
        return {
            "key": f"{self.provider_name}/{display_name}",
            "model_name": model_id,
            "provider": self,
        }
```

- [ ] **Step 4: Run the new tests — expect pass**

```bash
.venv/bin/python -m pytest tests/test_base_model_provider.py -v
```

Expected: all 6 PASS.

- [ ] **Step 5: Verify the full suite still passes**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS (providers will fail because `fetch_models` is now abstract-renamed — fix in Task 2).

---

## Task 2: Update all 5 providers to use the new base class API

**Files:**
- Modify: `models/anthropic_provider.py`
- Modify: `models/openai_provider.py`
- Modify: `models/google_provider.py`
- Modify: `models/groq_provider.py`
- Modify: `models/xai_provider.py`

> Each provider: rename `fetch_models` → `_do_fetch_models` and remove its inner try/except (the base class now handles it). Providers that use `get_fallback_models` with a plain list of IDs simplify to `_build_fallback_list`. Anthropic keeps its own `get_fallback_models` because it has display-name tuples.

- [ ] **Step 1: Update `models/anthropic_provider.py`**

Replace entire file:

```python
"""
Anthropic model provider - fetches and manages Anthropic Claude models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info

try:
    import anthropic as anthropic_sdk
except ImportError:
    anthropic_sdk = None


class AnthropicModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "anthropic"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = anthropic_sdk.Anthropic(api_key=api_key)
        temperature = self.default_temperature

        def call(prompt: str) -> str:
            message = client.messages.create(
                model=model_id,
                max_tokens=1024,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text

        return call

    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        if anthropic_sdk is None:
            raise ImportError("anthropic package not available")

        client = anthropic_sdk.Anthropic(api_key=self.api_key)
        models_page = client.models.list()

        model_names = {}
        for model in models_page.data:
            model_id = model.id
            display_name = getattr(model, 'display_name', model_id) or model_id
            if model_id and is_text_model(model_id, 'anthropic') and "claude" in model_id.lower():
                model_names[model_id] = display_name

        deduped = deduplicate_models(list(model_names.keys()))
        anthropic_models = [self.create_model_definition(m, model_names[m]) for m in deduped]
        info(f"Fetched {len(anthropic_models)} Anthropic Claude models dynamically")
        return anthropic_models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        fallback_models = [
            ("claude-3-5-sonnet-20241022", "Claude Sonnet 3.5"),
            ("claude-3-7-sonnet-20250219", "Claude Sonnet 3.7"),
            ("claude-sonnet-4-20250514", "Claude Sonnet 4"),
            ("claude-opus-4-20250514", "Claude Opus 4"),
            ("claude-3-5-haiku-20241022", "Claude Haiku 3.5"),
        ]
        return [
            self.create_model_definition(model_id, display_name)
            for model_id, display_name in fallback_models
            if is_text_model(model_id, 'anthropic')
        ]
```

- [ ] **Step 2: Update `models/openai_provider.py`**

Replace entire file:

```python
"""
OpenAI model provider - fetches and manages OpenAI models.
"""

from typing import List, Dict, Any, Callable

from openai import OpenAI

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info


class OpenAIModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "openai"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = OpenAI(api_key=api_key)
        temperature = self.default_temperature

        def call(prompt: str) -> str:
            completion = client.chat.completions.create(
                model=model_id,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content

        return call

    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        client = OpenAI(api_key=self.api_key)
        models = client.models.list()
        model_ids = [m.id for m in models.data if is_text_model(m.id, 'openai')]
        chat_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]
        info(f"Fetched {len(chat_models)} OpenAI chat models dynamically")
        return chat_models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        return self._build_fallback_list(
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        )
```

- [ ] **Step 3: Update `models/google_provider.py`**

Replace entire file:

```python
"""
Google Gemini model provider - fetches and manages Google AI models.
"""

import time
from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info, warning

try:
    from google import genai
except ImportError:
    genai = None


class GoogleModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "google"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = genai.Client(api_key=api_key)
        temperature = self.default_temperature

        def call(prompt: str) -> str:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=genai.types.GenerateContentConfig(temperature=temperature),
            )
            return response.text

        return call

    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        if genai is None:
            raise ImportError("google-genai package not available")

        client = genai.Client(api_key=self.api_key)

        max_retries = 3
        models = []
        for attempt in range(max_retries):
            try:
                models = list(client.models.list())
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                warning(
                    f"Attempt {attempt + 1} failed to fetch Google models: {e}. Retrying..."
                )
                time.sleep(2)

        model_ids = []
        for model in models:
            model_name = model.name.split('/')[-1] if '/' in model.name else model.name
            supported_actions = getattr(model, 'supported_actions', None)
            if (is_text_model(model_name, 'google') and "gemini" in model_name.lower() and
                    (supported_actions is None or 'generateContent' in supported_actions)):
                model_ids.append(model_name)

        google_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]
        info(f"Fetched {len(google_models)} Google Gemini models dynamically")
        return google_models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        return self._build_fallback_list([
            "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp",
            "gemini-2.5-flash", "gemini-2.5-pro",
        ])
```

- [ ] **Step 4: Update `models/groq_provider.py`**

Replace entire file:

```python
"""
Groq model provider - fetches and manages Groq models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info

try:
    from groq import Groq
except ImportError:
    Groq = None


class GroqModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "groq"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = Groq(api_key=api_key)
        temperature = self.default_temperature

        def call(prompt: str) -> str:
            completion = client.chat.completions.create(
                model=model_id,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content

        return call

    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        if Groq is None:
            raise ImportError("groq package not available")
        client = Groq(api_key=self.api_key)
        models = client.models.list()
        model_ids = [m.id for m in models.data if is_text_model(m.id, 'groq')]
        groq_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]
        info(f"Fetched {len(groq_models)} Groq models dynamically")
        return groq_models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        return self._build_fallback_list([
            "llama-3.1-70b-versatile", "llama-3.1-8b-instant",
            "llama3-70b-8192", "llama3-8b-8192",
            "mixtral-8x7b-32768", "gemma2-9b-it",
        ])
```

- [ ] **Step 5: Update `models/xai_provider.py`**

Replace entire file:

```python
"""
xAI model provider - fetches and manages xAI Grok models.
"""

from typing import List, Dict, Any, Callable

from xai_sdk import Client
from xai_sdk.chat import user as xai_user

from models.base_model_provider import BaseModelProvider
from models.model_filter import is_text_model, deduplicate_models
from utils.logger import info


class XAIModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "xai"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        client = Client(api_key=api_key)

        def call(prompt: str) -> str:
            chat = client.chat.create(model=model_id)
            chat.append(xai_user(prompt))
            response = chat.sample()
            return response.content

        return call

    def _do_fetch_models(self) -> List[Dict[str, Any]]:
        client = Client(api_key=self.api_key)
        language_models = client.models.list_language_models()
        model_ids = [
            m.name for m in language_models
            if is_text_model(m.name, 'xai')
        ]
        models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]
        info(f"Fetched {len(models)} xAI models dynamically")
        return models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        return self._build_fallback_list(["grok-4-0709", "grok-3", "grok-3-mini"])
```

- [ ] **Step 6: Run the full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS (including the 6 new base provider tests).

- [ ] **Step 7: Commit**

```bash
git add models/base_model_provider.py models/anthropic_provider.py \
        models/openai_provider.py models/google_provider.py \
        models/groq_provider.py models/xai_provider.py \
        tests/test_base_model_provider.py
git commit -m "refactor: extract fetch_models template and _build_fallback_list into BaseModelProvider"
```

---

## Task 3: Remove redundant `get_config()` call from `initialize_models()`

**Files:**
- Modify: `models/model_loader.py`

> `get_model_definitions()` already stores the provider instance (which holds `api_key`) in each model definition. `initialize_models()` currently calls `get_config()` a second time just to look up the same keys. We can read `api_key` directly from `md["provider"].api_key`.

- [ ] **Step 1: Replace `initialize_models()` in `models/model_loader.py`**

Replace only the `initialize_models` function (lines 77–116):

```python
def initialize_models() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Initialize all AI models from model definitions.
    Returns (initialized_models, initialization_errors).
    """
    initialized_models = {}
    initialization_errors = {}

    info("\n--- Initializing Models (from models/model_loader.py) ---")

    for provider_name, model_list in get_model_definitions().items():
        if not model_list:
            continue

        # api_key was already stored on the provider during get_model_definitions()
        api_key = model_list[0]["provider"].api_key

        if not api_key:
            warning(
                f"\n⚪ {provider_name.capitalize()} API Key not found, "
                f"skipping {provider_name} models."
            )
            for md in model_list:
                initialization_errors[md["key"]] = (
                    f"{provider_name.capitalize()} API Key not found."
                )
            continue

        info(f"\n-- Initializing {provider_name.capitalize()} models --")
        for md in model_list:
            model_key = md["key"]
            provider = md["provider"]
            try:
                initialized_models[model_key] = provider.build_callable(
                    md["model_name"], api_key
                )
                info(f"✅ Initialized {model_key}")
            except Exception as e:
                err = f"Failed to initialize {model_key}: {e}"
                initialization_errors[model_key] = err
                error(f"❌ {err}")

    info("\n--- Model Initialization Complete ---")
    if initialization_errors:
        warning("Some models failed to initialize. They will not be available for selection.")

    return initialized_models, initialization_errors
```

Also remove the now-unused import at the top of `model_loader.py`. Currently line 9 reads:
```python
from config.config_manager import get_config
```
`get_config` is still used in `get_model_definitions()` (line 45), so **keep this import**.

- [ ] **Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add models/model_loader.py
git commit -m "refactor: read api_key from provider object in initialize_models, remove second get_config call"
```

---

## Task 4: Fix `process_text()` exception handling

**Files:**
- Modify: `core/app_manager.py`

> Replace the merged `except (ProcessingError, Exception)` with two separate clauses, matching the pattern in `TaskProcessor.execute_task()`.

- [ ] **Step 1: Replace the `except` block in `process_text()`**

In `core/app_manager.py`, replace:

```python
        except (ProcessingError, Exception) as e:
            error_msg = handle_error(e, "Text processing")
            self.last_result = None
            self.last_result_task_id = None
            self.last_result_is_error = True
            prefix = "" if isinstance(e, ProcessingError) else "Unexpected "
            return f"{prefix}Error: {error_msg}"
```

With:

```python
        except ProcessingError as e:
            error_msg = handle_error(e, "Text processing")
            self.last_result = None
            self.last_result_task_id = None
            self.last_result_is_error = True
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = handle_error(e, "Text processing")
            self.last_result = None
            self.last_result_task_id = None
            self.last_result_is_error = True
            return f"Unexpected error: {error_msg}"
```

- [ ] **Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS. `test_process_text_processing_error` already asserts `"Error:" in result` which matches both clauses.

- [ ] **Step 3: Commit**

```bash
git add core/app_manager.py
git commit -m "refactor: split merged except clause in process_text to match TaskProcessor pattern"
```

---

## Task 5: Add circuit breaker integration tests

**Files:**
- Modify: `tests/test_app_manager.py`

> `CircuitBreaker` is unit-tested in `tests/test_error_handler.py`. What's missing is the *integration* between `TaskProcessor.execute_task()` and the circuit breaker: verifying that repeated failures open the circuit and that an open circuit raises `ProcessingError` without calling the model.

- [ ] **Step 1: Add tests to `TestTaskProcessor` in `tests/test_app_manager.py`**

Add these three test methods inside `class TestTaskProcessor`, after `test_execute_task_auto_translate`:

```python
    def test_circuit_breaker_opens_after_threshold_failures(
        self, task_processor, mock_get_model
    ):
        # Default threshold is 3 failures
        mock_model = Mock(side_effect=RuntimeError("API down"))
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            for _ in range(3):
                with pytest.raises(ProcessingError):
                    task_processor.execute_task('test_model', 'input', 'refine')

        cb = task_processor.circuit_breakers['test_model']
        from utils.error_handler import CircuitBreaker
        assert cb.state == CircuitBreaker.STATE_OPEN

    def test_open_circuit_raises_without_calling_model(
        self, task_processor, mock_get_model
    ):
        from utils.error_handler import CircuitBreaker, APIError
        mock_model = Mock(side_effect=RuntimeError("API down"))
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            for _ in range(3):
                with pytest.raises(ProcessingError):
                    task_processor.execute_task('test_model', 'input', 'refine')

        # 4th call — circuit is open, model should NOT be called
        mock_model.reset_mock()
        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            with pytest.raises(ProcessingError) as exc_info:
                task_processor.execute_task('test_model', 'input', 'refine')

        mock_model.assert_not_called()
        assert isinstance(exc_info.value.original_error, APIError)

    def test_each_model_key_has_independent_circuit_breaker(
        self, task_processor, mock_get_model
    ):
        failing_model = Mock(side_effect=RuntimeError("down"))
        passing_model = Mock(return_value="ok")

        def get_model(key):
            return failing_model if key == 'bad_model' else passing_model

        mock_get_model.side_effect = get_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            for _ in range(3):
                with pytest.raises(ProcessingError):
                    task_processor.execute_task('bad_model', 'input', 'refine')

            # good_model has its own circuit breaker — should still work
            result = task_processor.execute_task('good_model', 'input', 'refine')

        assert result == "ok"
        assert 'bad_model' in task_processor.circuit_breakers
        assert 'good_model' in task_processor.circuit_breakers
```

- [ ] **Step 2: Run the new tests**

```bash
.venv/bin/python -m pytest tests/test_app_manager.py::TestTaskProcessor -v
```

Expected: all 8 tests in `TestTaskProcessor` PASS (3 new + 5 existing).

- [ ] **Step 3: Commit**

```bash
git add tests/test_app_manager.py
git commit -m "test: add circuit breaker integration tests for TaskProcessor"
```

---

## Task 6: Add prompt formatting edge-case tests

**Files:**
- Modify: `tests/test_app_manager.py`

> `execute_task()` calls `prompt_template_str.format(user_text=text_input)`. Verify that user input containing curly braces is passed through correctly and does not cause a `KeyError`.

- [ ] **Step 1: Add the test to `TestTaskProcessor` in `tests/test_app_manager.py`**

Add inside `class TestTaskProcessor`, after the circuit breaker tests:

```python
    def test_prompt_format_passes_through_curly_braces_in_input(
        self, task_processor, mock_get_model
    ):
        # User input may contain JSON or template-like strings with braces.
        # str.format() should substitute {user_text} in the template and leave
        # braces inside the substituted value untouched.
        mock_model = Mock(return_value="done")
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Refine: {user_text}"
            result = task_processor.execute_task(
                'test_model', '{"key": "value"}', 'refine'
            )

        assert result == "done"
        mock_model.assert_called_once_with('Refine: {"key": "value"}')
```

- [ ] **Step 2: Run the test**

```bash
.venv/bin/python -m pytest tests/test_app_manager.py::TestTaskProcessor::test_prompt_format_passes_through_curly_braces_in_input -v
```

Expected: PASS.

- [ ] **Step 3: Run the full suite**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_app_manager.py
git commit -m "test: verify curly braces in user input pass through prompt formatting safely"
```

---

## Task 7: Document the model definition cache

**Files:**
- Modify: `models/model_loader.py`

> The `_model_cache` is not needed for the main application (which calls `initialize_models()` once at startup), but is valuable when scripts call `get_model_definitions()` directly during development. Add a comment to make this intent explicit.

- [ ] **Step 1: Update the `get_model_definitions` docstring**

In `models/model_loader.py`, replace:

```python
def get_model_definitions() -> Dict[str, list]:
    """
    Fetch model definitions from all providers with 1-hour caching.
    Falls back to predefined models when API calls fail.
    """
```

With:

```python
def get_model_definitions() -> Dict[str, list]:
    """
    Fetch model definitions from all providers with 1-hour caching.
    Falls back to predefined models when API calls fail.

    The cache is unused during normal app startup (initialize_models calls
    this once). It benefits scripts/tools that call this function repeatedly
    in a single process (e.g. scripts/test_providers.py).
    """
```

- [ ] **Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add models/model_loader.py
git commit -m "docs: clarify why model definition cache exists in model_loader"
```

---

## Self-Review

**Spec coverage check:**

| Optimization | Task |
|---|---|
| Extract `fetch_models()` template into base | Task 1 + 2 |
| Extract `_build_fallback_list()` helper | Task 1 + 2 |
| Remove second `get_config()` call | Task 3 |
| Fix merged `except` in `process_text()` | Task 4 |
| Circuit breaker integration tests | Task 5 |
| Prompt formatting edge-case test | Task 6 |
| Document model cache purpose | Task 7 |

All 8 optimization items are covered. ✓

**Placeholder scan:** No TBD, TODO, or "similar to Task N" references. Every code block is complete. ✓

**Type consistency:**
- `_do_fetch_models()` defined in Task 1 as `-> List[Dict[str, Any]]`, used in Task 2 for all 5 providers ✓
- `_build_fallback_list(model_ids: List[str])` defined in Task 1, used in Task 2 for openai/google/groq/xai ✓
- `provider.api_key` (str) used in Task 3 — this attribute is set in `BaseModelProvider.__init__` ✓
- `CircuitBreaker.STATE_OPEN` string constant used in Task 5 — defined in `utils/error_handler.py:84` ✓
- `APIError` imported in Task 5 tests from `utils.error_handler` — defined there ✓
