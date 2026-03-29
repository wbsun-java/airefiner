# LangChain Removal — Native SDK Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all LangChain packages and replace with official provider SDKs, keeping app behaviour identical.

**Architecture:** `_models[key]` changes from LangChain chat objects to `Callable[[str], str]` closures. Each provider's `build_callable(model_id, api_key)` creates the closure using its native SDK. `execute_task()` formats the prompt with Python `.format()` and calls the callable directly.

**Tech Stack:** `anthropic`, `openai`, `google-genai`, `groq`, `xai-sdk` (all already in the repo)

---

## File Map

| File | Change |
|---|---|
| `tests/test_app_manager.py` | Remove LangChain patches; mock models as plain callables |
| `core/app_manager.py` | Drop chain pipeline; use `.format()` + direct callable |
| `models/base_model_provider.py` | Replace `get_model_class()`/`get_model_id_key()` with `build_callable()` |
| `models/anthropic_provider.py` | Implement `build_callable()` via `anthropic` SDK |
| `models/openai_provider.py` | Implement `build_callable()` via `openai` SDK |
| `models/google_provider.py` | Implement `build_callable()` via `google-genai` SDK |
| `models/groq_provider.py` | Implement `build_callable()` via `groq` SDK |
| `models/xai_provider.py` | Implement `build_callable()` via `xai-sdk` |
| `models/model_loader.py` | Call `provider.build_callable()` instead of `model_class(**args)` |
| `config/config_manager.py` | Remove `_API_KEY_ARG_NAMES` and `api_key_arg_names` field |
| `requirements.txt` | Drop 5 `langchain-*` packages; pin official SDK versions |
| `.claude/rules/configuration.md` | Remove `_API_KEY_ARG_NAMES` mention |
| `.claude/rules/design-patterns.md` | Update provider contract and xAI sections |
| `.claude/rules/testing.md` | Update patch path documentation |

---

## Task 1: Update tests — callable interface

**Files:**
- Modify: `tests/test_app_manager.py`

- [ ] **Step 1: Replace the three LangChain-patched tests**

Open `tests/test_app_manager.py`. Replace `test_execute_task_success`, `test_execute_task_chain_exception`, and `test_execute_task_auto_translate` with the versions below. Remove all `@patch('langchain_core.*')` decorators from the file.

```python
def test_execute_task_success(self, task_processor, mock_get_model):
    mock_model = Mock(return_value="Processed text")
    mock_get_model.return_value = mock_model

    with patch('prompts.refine_prompts') as mock_prompts:
        mock_prompts.REFINE_TEXT_PROMPT = "Test prompt: {user_text}"
        result = task_processor.execute_task('test_model', 'input text', 'refine')

    assert result == "Processed text"
    mock_model.assert_called_once_with("Test prompt: input text")

def test_execute_task_chain_exception(self, task_processor, mock_get_model):
    mock_model = Mock(side_effect=RuntimeError("API call failed"))
    mock_get_model.return_value = mock_model

    with patch('prompts.refine_prompts') as mock_prompts:
        mock_prompts.REFINE_TEXT_PROMPT = "Test prompt: {user_text}"
        with pytest.raises(ProcessingError) as exc_info:
            task_processor.execute_task('test_model', 'input text', 'refine')

    assert exc_info.value.task_id == 'refine'
    assert isinstance(exc_info.value.original_error, RuntimeError)

@patch('utils.translation_handler.TranslationHandler')
def test_execute_task_auto_translate(self, mock_handler_cls, task_processor, mock_get_model):
    mock_model = Mock(return_value="Translated text")
    mock_get_model.return_value = mock_model

    mock_handler = Mock()
    mock_handler_cls.return_value = mock_handler
    mock_handler.get_translation_prompt.return_value = "Translation prompt: {user_text}"

    result = task_processor.execute_task('test_model', 'input text', 'auto_translate')

    assert result == "Translated text"
    mock_handler.get_translation_prompt.assert_called_once_with('input text')
    mock_model.assert_called_once_with("Translation prompt: input text")
```

- [ ] **Step 2: Run tests — expect failures**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: `test_execute_task_success`, `test_execute_task_chain_exception`, `test_execute_task_auto_translate` FAIL. The other tests may pass or fail depending on whether `langchain_core` is installed. That's fine — we fix it next.

---

## Task 2: Update `execute_task` — drop the chain

**Files:**
- Modify: `core/app_manager.py`

- [ ] **Step 1: Replace `execute_task` body**

In `core/app_manager.py`, replace the entire `execute_task` method with:

```python
def execute_task(self, model_key: str, text_input: str, task_id: str) -> str:
    try:
        if model_key not in self.circuit_breakers:
            self.logger.info(f"Creating new circuit breaker for model '{model_key}'")
            self.circuit_breakers[model_key] = CircuitBreaker(name=model_key)
        circuit_breaker = self.circuit_breakers[model_key]

        from prompts import refine_prompts

        model_callable = self.get_model(model_key)
        if not model_callable:
            raise ProcessingError(f"Model '{model_key}' not found", task_id)

        if task_id == TaskConfiguration.AUTO_TRANSLATE:
            if self._translation_handler is None:
                from utils.translation_handler import TranslationHandler
                self._translation_handler = TranslationHandler()
            prompt_template_str = self._translation_handler.get_translation_prompt(text_input)
        else:
            prompt_map = {
                TaskConfiguration.REFINE: refine_prompts.REFINE_TEXT_PROMPT,
                TaskConfiguration.REFINE_PRESENTATION: refine_prompts.REFINE_PRESENTATION_PROMPT,
            }
            prompt_template_str = prompt_map.get(task_id)

        if not prompt_template_str:
            raise ProcessingError(f"Prompt for task '{task_id}' not found", task_id)

        formatted_prompt = prompt_template_str.format(user_text=text_input)

        self.logger.info(f"Executing task '{task_id}' with model '{model_key}'")
        result = circuit_breaker.call(model_callable, formatted_prompt)
        self.logger.info("Task execution completed successfully")
        return result

    except ProcessingError:
        raise
    except Exception as e:
        error_msg = handle_error(e, f"Task execution ({task_id})")
        raise ProcessingError(error_msg, task_id, e)
```

The only changes from the original are:
- Removed `from langchain_core.prompts import ChatPromptTemplate`
- Removed `from langchain_core.output_parsers import StrOutputParser`
- Removed `output_parser = StrOutputParser()`
- Replaced `ChatPromptTemplate.from_template(...)` with `prompt_template_str.format(user_text=text_input)`
- Replaced `circuit_breaker.call(chain.invoke, {"user_text": text_input})` with `circuit_breaker.call(model_callable, formatted_prompt)`

- [ ] **Step 2: Run tests — expect pass**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL tests PASS.

- [ ] **Step 3: Commit**

```bash
git add core/app_manager.py tests/test_app_manager.py
git commit -m "refactor: replace LangChain chain with native callable in execute_task"
```

---

## Task 3: Update `base_model_provider.py` — new contract

**Files:**
- Modify: `models/base_model_provider.py`

- [ ] **Step 1: Replace the file content**

```python
"""
Base classes for model providers to eliminate code duplication.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

from config.constants import DEFAULT_TEMPERATURE
from utils.logger import LoggerMixin


class BaseModelProvider(ABC, LoggerMixin):
    """
    Base class for all model providers.
    """

    def __init__(self, api_key: str, provider_name: str):
        self.api_key = api_key
        self.provider_name = provider_name
        self.default_temperature = DEFAULT_TEMPERATURE

    @abstractmethod
    def fetch_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        """
        Return a callable that accepts a formatted prompt string and returns
        the model's text response.
        """
        pass

    def create_model_definition(self, model_id: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        if display_name is None:
            display_name = model_id
        return {
            "key": f"{self.provider_name}/{display_name}",
            "model_name": model_id,
            "provider": self,
        }
```

- [ ] **Step 2: Verify tests still pass**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS (tests don't import base provider directly).

- [ ] **Step 3: Commit**

```bash
git add models/base_model_provider.py
git commit -m "refactor: replace get_model_class/get_model_id_key with build_callable in BaseModelProvider"
```

---

## Task 4: Update `anthropic_provider.py`

**Files:**
- Modify: `models/anthropic_provider.py`

- [ ] **Step 1: Replace the file content**

```python
"""
Anthropic model provider - fetches and manages Anthropic Claude models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error

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

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models

        try:
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

        except Exception as e:
            error(f"Failed to fetch Anthropic models: {e}")
            info("Falling back to predefined Claude models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

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

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add models/anthropic_provider.py
git commit -m "refactor: migrate AnthropicModelProvider to native anthropic SDK"
```

---

## Task 5: Update `openai_provider.py`

**Files:**
- Modify: `models/openai_provider.py`

- [ ] **Step 1: Replace the file content**

```python
"""
OpenAI model provider - fetches and manages OpenAI models.
"""

from typing import List, Dict, Any, Callable

from openai import OpenAI

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error


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

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models

        try:
            client = OpenAI(api_key=self.api_key)
            models = client.models.list()

            model_ids = [m.id for m in models.data if is_text_model(m.id, 'openai')]
            chat_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]

            info(f"Fetched {len(chat_models)} OpenAI chat models dynamically")
            return chat_models

        except Exception as e:
            error(f"Failed to fetch OpenAI models: {e}")
            info("Falling back to predefined models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

        model_ids = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'openai')
        ]
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add models/openai_provider.py
git commit -m "refactor: migrate OpenAIModelProvider to native openai SDK"
```

---

## Task 6: Update `google_provider.py`

**Files:**
- Modify: `models/google_provider.py`

- [ ] **Step 1: Replace the file content**

```python
"""
Google Gemini model provider - fetches and manages Google AI models.
"""

import time
from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from utils.logger import info, warning, error

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

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models

        try:
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
                    if attempt < max_retries - 1:
                        warning(f"Attempt {attempt + 1} failed to fetch Google models: {e}. Retrying...")
                        time.sleep(2)
                    else:
                        raise e

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

        except Exception as e:
            error(f"Failed to fetch Google models: {e}")
            info("Falling back to predefined Gemini models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

        model_ids = [
            "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp",
            "gemini-2.5-flash", "gemini-2.5-pro",
        ]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'google')
        ]
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add models/google_provider.py
git commit -m "refactor: migrate GoogleModelProvider to native google-genai SDK"
```

---

## Task 7: Update `groq_provider.py`

**Files:**
- Modify: `models/groq_provider.py`

- [ ] **Step 1: Replace the file content**

```python
"""
Groq model provider - fetches and manages Groq models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error

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

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models

        try:
            if Groq is None:
                raise ImportError("groq package not available")

            client = Groq(api_key=self.api_key)
            models = client.models.list()

            model_ids = [m.id for m in models.data if is_text_model(m.id, 'groq')]
            groq_models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]

            info(f"Fetched {len(groq_models)} Groq models dynamically")
            return groq_models

        except Exception as e:
            error(f"Failed to fetch Groq models: {e}")
            info("Falling back to predefined Groq models")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

        model_ids = [
            "llama-3.1-70b-versatile", "llama-3.1-8b-instant",
            "llama3-70b-8192", "llama3-8b-8192",
            "mixtral-8x7b-32768", "gemma2-9b-it",
        ]
        return [
            self.create_model_definition(model_id)
            for model_id in model_ids
            if is_text_model(model_id, 'groq')
        ]
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add models/groq_provider.py
git commit -m "refactor: migrate GroqModelProvider to native groq SDK"
```

---

## Task 8: Update `xai_provider.py`

**Files:**
- Modify: `models/xai_provider.py`

- [ ] **Step 1: Replace the file content**

```python
"""
xAI model provider - fetches and manages xAI Grok models.
"""

from typing import List, Dict, Any, Callable

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error


class XAIModelProvider(BaseModelProvider):

    def __init__(self, api_key: str, provider_name: str = "xai"):
        super().__init__(api_key, provider_name)

    def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
        from xai_sdk import Client
        from xai_sdk.chat import user as xai_user

        client = Client(api_key=api_key)

        def call(prompt: str) -> str:
            chat = client.chat.create(model=model_id)
            chat.append(xai_user(prompt))
            response = chat.sample()
            return response.content

        return call

    def fetch_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model, deduplicate_models

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1")
            model_ids = [
                m.id for m in client.models.list().data
                if is_text_model(m.id, 'xai')
            ]
            models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]
            info(f"Fetched {len(models)} xAI models dynamically")
            return models
        except Exception as e:
            error(f"Failed to fetch xAI models: {e}")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        from models.model_filter import is_text_model

        model_ids = ["grok-4-0709", "grok-3", "grok-3-mini"]
        return [self.create_model_definition(m) for m in model_ids
                if is_text_model(m, 'xai')]
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add models/xai_provider.py
git commit -m "refactor: migrate XAIModelProvider to native xai-sdk"
```

---

## Task 9: Update `model_loader.py`

**Files:**
- Modify: `models/model_loader.py`

- [ ] **Step 1: Replace `initialize_models()`**

Replace the entire `initialize_models` function with:

```python
def initialize_models() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Initialize all AI models from model definitions.
    Returns (initialized_models, initialization_errors).
    """
    initialized_models = {}
    initialization_errors = {}

    info("\n--- Initializing Models (from models/model_loader.py) ---")

    config = get_config()
    api_keys = config.api_config.get_api_keys()

    for provider_name, model_list in get_model_definitions().items():
        api_key = api_keys.get(provider_name)

        if not api_key:
            warning(f"\n⚪ {provider_name.capitalize()} API Key not found, skipping {provider_name} models.")
            for md in model_list:
                initialization_errors[md["key"]] = f"{provider_name.capitalize()} API Key not found."
            continue

        info(f"\n-- Initializing {provider_name.capitalize()} models --")
        for md in model_list:
            model_key = md["key"]
            provider = md["provider"]

            try:
                initialized_models[model_key] = provider.build_callable(md["model_name"], api_key)
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

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_app_manager.py -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add models/model_loader.py
git commit -m "refactor: update initialize_models to use provider.build_callable"
```

---

## Task 10: Update `config_manager.py`

**Files:**
- Modify: `config/config_manager.py`

- [ ] **Step 1: Remove `_API_KEY_ARG_NAMES` and the field that uses it**

In `config/config_manager.py`:

Delete this block (lines 21–27):
```python
_API_KEY_ARG_NAMES: Dict[str, str] = {
    ModelProvider.OPENAI.value: "openai_api_key",
    ModelProvider.ANTHROPIC.value: "anthropic_api_key",
    ModelProvider.GOOGLE.value: "google_api_key",
    ModelProvider.GROQ.value: "groq_api_key",
    ModelProvider.XAI.value: "xai_api_key",
}
```

In the `APIConfiguration` dataclass, delete this field:
```python
    api_key_arg_names: Dict[str, str] = field(default_factory=_API_KEY_ARG_NAMES.copy)
```

Also remove the unused `field` import from `dataclasses` if `field` is no longer used anywhere in the file. Check — `field` is only used for `api_key_arg_names`, so remove it:

Change:
```python
from dataclasses import dataclass, field
```
To:
```python
from dataclasses import dataclass
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/ -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add config/config_manager.py
git commit -m "refactor: remove _API_KEY_ARG_NAMES from config (no longer needed after LangChain removal)"
```

---

## Task 11: Update `requirements.txt`

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Replace the file content**

```
# Core AI — Official Provider SDKs
anthropic>=0.86.0
openai>=2.30.0
google-genai>=1.69.0
groq>=1.1.2
xai-sdk>=1.11.0

# Utilities
python-dotenv>=1.2.1
requests>=2.32.5
langdetect>=1.0.9
```

- [ ] **Step 2: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: remove langchain-* packages, pin official provider SDK versions"
```

---

## Task 12: Update rule files

**Files:**
- Modify: `.claude/rules/configuration.md`
- Modify: `.claude/rules/design-patterns.md`
- Modify: `.claude/rules/testing.md`

- [ ] **Step 1: Update `configuration.md`**

Replace the entire file content with:

```markdown
API keys are loaded from `.env` via `python-dotenv`. Supported variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`. At least one must be set.

`config/config_manager.py` holds the `TASKS` dict (maps menu numbers `"1"–"3"` to task dicts). This must stay in sync with `TaskConfiguration` constants in `config/constants.py`.
```

- [ ] **Step 2: Update `design-patterns.md`**

Replace the **Provider contract** paragraph:

Old:
```
**Provider contract** (`models/base_model_provider.py`): Every provider implements `fetch_models()`, `get_fallback_models()`, `get_model_class()`, and `get_model_id_key()`. The `create_model_definition()` base method produces the standardized dict (`key`, `model_name`, `class`, `args`, `model_id_key`) consumed by `initialize_models()`.
```

New:
```
**Provider contract** (`models/base_model_provider.py`): Every provider implements `fetch_models()`, `get_fallback_models()`, and `build_callable(model_id, api_key) -> Callable[[str], str]`. The `create_model_definition()` base method produces the standardized dict (`key`, `model_name`, `provider`) consumed by `initialize_models()`.
```

Replace the **xAI** paragraph:

Old:
```
**xAI uses the official `langchain-xai` integration**: `models/xai_provider.py` imports `ChatXAI` from `langchain_xai` (which extends `BaseChatOpenAI` and uses the OpenAI-compatible REST API at `https://api.x.ai/v1`). Model listing uses the `openai` client pointed at the same base URL.
```

New:
```
**xAI uses the native `xai-sdk`**: `models/xai_provider.py` imports `Client` from `xai_sdk` and uses the chat builder pattern (`client.chat.create` → `chat.append(user(...))` → `chat.sample()`). Model listing still uses the `openai` client pointed at `https://api.x.ai/v1`.
```

- [ ] **Step 3: Update `testing.md`**

Replace the entire file content with:

```markdown
Tests in `tests/test_app_manager.py` patch `prompts.refine_prompts` at its source module path (not at `core.app_manager.*`). This works because `execute_task()` uses a deferred import. Do not move those imports to module level — it breaks the patches.

Model objects in `_models` are `Callable[[str], str]`. In tests, use `Mock(return_value="some text")` as the model — the mock is called with the fully-formatted prompt string.
```

- [ ] **Step 4: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add .claude/rules/configuration.md .claude/rules/design-patterns.md .claude/rules/testing.md
git commit -m "docs: update rule files to reflect LangChain removal"
```

---

## Task 13: Integration smoke test

- [ ] **Step 1: Verify the app starts and loads models**

With real API keys in `.env`, run:

```bash
python3 scripts/test_providers.py
```

Expected: All providers with valid API keys report successful model fetch. No `langchain` import errors.

- [ ] **Step 2: Verify no LangChain imports remain**

```bash
grep -r "langchain" . --include="*.py" --exclude-dir=.venv
```

Expected: zero matches.

- [ ] **Step 3: Verify no LangChain in requirements**

```bash
grep "langchain" requirements.txt
```

Expected: zero matches.

- [ ] **Step 4: Final test run**

```bash
python3 -m pytest tests/ -v
```

Expected: ALL PASS.
