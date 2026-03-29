# Design: Remove LangChain, Migrate to Official Provider SDKs

**Date:** 2026-03-29
**Status:** Approved

## Goal

Remove all LangChain packages (`langchain`, `langchain-core`, `langchain-anthropic`, `langchain-google-genai`, `langchain-groq`, `langchain-openai`, `langchain-xai`) and replace them with the official first-party SDKs already present in the project. The application behavior and prompt content are unchanged.

## Packages

### Removed
- `langchain`
- `langchain-anthropic`
- `langchain-google-genai`
- `langchain-groq`
- `langchain-openai`
- `langchain-xai` (currently missing from requirements.txt anyway)

### Kept (official SDKs)
- `anthropic` — Anthropic official Python SDK
- `openai` — OpenAI official Python SDK (also used for xAI model listing)
- `google-genai` — Google official GenAI SDK
- `groq` — Groq official Python SDK
- `xai-sdk` — xAI official Python SDK (used for inference)

## Architecture Changes

### `execute_task()` — `core/app_manager.py`

**Before:** LangChain chain pipeline
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt_template = ChatPromptTemplate.from_template(prompt_str)
chain = prompt_template | model_instance | output_parser
result = circuit_breaker.call(chain.invoke, {"user_text": text_input})
```

**After:** Plain Python
```python
formatted_prompt = prompt_str.format(user_text=text_input)
result = circuit_breaker.call(model_callable, formatted_prompt)
```

`_models[key]` stores a `Callable[[str], str]` instead of a LangChain object.

### Prompt format

Prompts in `prompts/refine_prompts.py` and `utils/translation_handler.py` are unchanged — they remain single combined strings with `{user_text}` placeholder. The entire formatted string is sent as a single user message to each provider.

### `base_model_provider.py`

`get_model_class()` and `get_model_id_key()` are removed. A new abstract method replaces them:

```python
@abstractmethod
def build_callable(self, model_id: str, api_key: str) -> Callable[[str], str]:
    """Return a callable that accepts a formatted prompt and returns the model's text response."""
```

`create_model_definition()` drops the `class`, `args`, and `model_id_key` fields. It keeps `key` and `model_name`, and adds a reference to the provider instance so `model_loader` can call `build_callable`.

### Provider files (one change each)

Each provider implements `build_callable()` using its native SDK. The client is initialized inside the closure (once per model).

| Provider | SDK call | Response extraction |
|---|---|---|
| Anthropic | `client.messages.create(model=..., max_tokens=1024, messages=[{"role":"user","content":prompt}])` | `.content[0].text` |
| OpenAI | `client.chat.completions.create(model=..., messages=[{"role":"user","content":prompt}])` | `.choices[0].message.content` |
| Google | `client.models.generate_content(model=..., contents=prompt)` | `.text` |
| Groq | `client.chat.completions.create(model=..., messages=[{"role":"user","content":prompt}])` | `.choices[0].message.content` |
| xAI | `chat = client.chat.create(model=...); chat.append(user(prompt)); chat.sample()` | `.content` |

`fetch_models()` and `get_fallback_models()` are unchanged — they already use native SDKs for model listing.

### `model_loader.py` — `initialize_models()`

**Before:**
```python
model_class = md["class"]
args = md["args"].copy()
args[api_key_arg_name] = api_key
args[model_id_key] = md["model_name"]
initialized_models[model_key] = model_class(**args)
```

**After:**
```python
provider = md["provider"]
initialized_models[model_key] = provider.build_callable(md["model_name"], api_key)
```

`api_key_arg_names` in `config/config_manager.py` is no longer needed for model initialization (it was only used to map provider names to LangChain constructor keyword arguments). It can be removed.

### Tests — `tests/test_app_manager.py`

LangChain-specific patches are removed:
- `@patch('langchain_core.prompts.ChatPromptTemplate')`
- `@patch('langchain_core.output_parsers.StrOutputParser')`

The model returned by `mock_get_model` becomes a plain callable mock:
```python
mock_model = Mock(return_value="Processed text")
mock_get_model.return_value = mock_model
```

All other test assertions remain the same.

## Files Changed

| File | Change |
|---|---|
| `requirements.txt` | Remove 5 langchain-* packages |
| `core/app_manager.py` | Replace chain with `.format()` + direct callable |
| `models/base_model_provider.py` | Replace `get_model_class()` / `get_model_id_key()` with `build_callable()` |
| `models/anthropic_provider.py` | Implement `build_callable()` using `anthropic` SDK |
| `models/openai_provider.py` | Implement `build_callable()` using `openai` SDK |
| `models/google_provider.py` | Implement `build_callable()` using `google-genai` SDK |
| `models/groq_provider.py` | Implement `build_callable()` using `groq` SDK |
| `models/xai_provider.py` | Implement `build_callable()` using `xai-sdk` |
| `models/model_loader.py` | Call `provider.build_callable()` instead of `model_class(**args)` |
| `config/config_manager.py` | Remove `_API_KEY_ARG_NAMES` dict and `api_key_arg_names` field from `APIConfiguration` |
| `tests/test_app_manager.py` | Remove LangChain patches; use plain callable mocks |
| `.claude/rules/configuration.md` | Remove mention of `_API_KEY_ARG_NAMES` |

## Out of Scope

- Prompt content changes
- Streaming support
- System/user message splitting
- Any other features
