# AIRefiner

A console AI-powered text processing tool for **refining, translating, and improving business communications**. Features a clean layered architecture, dynamic model fetching from 4 AI providers (native SDKs), intelligent model filtering, and automatic English ↔ Chinese language detection with task continuity.

## Program Objective

AIRefiner serves three main purposes:

1. **Text Refinement**: Transform informal text into professional, polished communications
2. **Presentation Enhancement**: Convert basic content into presentation-ready talking points
3. **Intelligent Translation**: Automatic language detection with bidirectional English ↔ Chinese translation

The program offers previous-result improvement only when continuing with the same task type.

## Core Features

### AI Provider Integration
- **Dynamic Model Fetching**: Real-time model discovery from OpenAI, Google, Anthropic, and xAI
- **Native SDKs**: Official provider packages (`openai`, `google-genai`, `anthropic`, `xai-sdk`) — no LangChain
- **Intelligent Filtering**: Excludes non-text model types (image, audio, video, embedding, code, moderation, safety models)
- **Fallback System**: Predefined models when dynamic fetching fails

### Architecture
- **Clean Separation**: UI layer → business logic → configuration → provider integration
- **State Management**: Tracks selected models, tasks, and last results
- **Circuit Breaker**: Prevents repeated calls to failing models
- **Error Recovery**: Context-aware user-facing error messages

### Smart Translation System
- **Automatic Detection**: Uses `langdetect` for language identification
- **Fallback Logic**: Defaults to text refinement for unsupported languages
- **Bidirectional Support**: Chinese (Simplified/Traditional) ↔ English

## Project Structure

```
airefiner/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── pytest.ini                 # Test configuration
├── .env                       # API keys (user-created, not in repo)
│
├── config/                    # Configuration management
│   ├── constants.py           # Application constants, enums, filtering rules
│   └── config_manager.py      # API keys, tasks, validation
│
├── core/                      # Business logic layer
│   └── app_manager.py         # ApplicationManager + TaskProcessor
│
├── ui/                        # User interface layer
│   └── console_interface.py   # Console UI with grouped model display
│
├── models/                    # AI model management
│   ├── model_loader.py        # Orchestrator: fetch, cache, initialize
│   ├── base_model_provider.py # Abstract base class for providers
│   ├── openai_provider.py     # OpenAI (GPT)
│   ├── google_provider.py     # Google (Gemini)
│   ├── anthropic_provider.py  # Anthropic (Claude)
│   ├── xai_provider.py        # xAI (Grok via xai-sdk)
│   └── model_filter.py        # Text-model filtering and deduplication
│
├── prompts/                   # Prompt templates
│   ├── refine_prompts.py      # Text refinement and presentation prompts
│   └── translate_prompts.py   # Translation prompts (EN ↔ ZH)
│
├── utils/                     # Shared helpers
│   ├── input_helpers.py       # Multi-line input handling
│   ├── translation_handler.py # Language detection and auto-translation
│   ├── logger.py              # Structured console logging
│   └── error_handler.py       # Exceptions, circuit breaker
│
├── tests/                     # Unit tests (pytest)
│   ├── conftest.py
│   ├── test_app_manager.py
│   ├── test_base_model_provider.py
│   ├── test_config_manager.py
│   └── test_error_handler.py
│
└── docs/                      # Design notes and plans
    └── superpowers/           # Specs and implementation plans
```

## Installation

### 1. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create a `.env` file with your API keys

```env
# Add keys ONLY for the services you have access to (at least one required)
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_xai_key_here
```

### 3. Verify with unit tests

```bash
python3 -m pytest tests/
```

## Usage

### Run the application

```bash
python3 main.py
```

### Run tests

```bash
# Full unit suite
python3 -m pytest tests/

# Single file
python3 -m pytest tests/test_app_manager.py

# Single test
python3 -m pytest tests/test_app_manager.py::TestTaskProcessor::test_execute_task_success
```

Live provider calls require real API keys in `.env` and are not part of the default unit suite.

## Available Tasks

### 1. Text Refinement
Transform informal text into professional, polished communications (emails, messages, documents, articles).

### 2. Presentation Enhancement
Convert basic content into presentation-ready talking points with professional structure.

### 3. Intelligent Auto-Translation
Automatic language detection with intelligent translation direction:
- English detected → Translate to Simplified Chinese
- Chinese detected → Translate to English
- Other / unknown → Fallback to Text Refinement

## Configuration

### API Keys

Set API keys via environment variables or a `.env` file in the project root. Only keys for services you use are required. At least one must be set.

### Model Filtering

The system automatically filters out non-text models (image, audio, video, embedding, code, moderation, etc.). Filtering rules are defined in `config/constants.py` under `ModelFiltering`.

### Logging

- Console-only logging (no log files by default)
- Color-coded output with Windows Unicode safety for emoji

## Architecture Overview

```
main.py (AIRefinerApp)
  └── ui/console_interface.py      # All user I/O — no business logic
  └── core/app_manager.py          # ApplicationManager + TaskProcessor — no I/O
        └── models/model_loader.py # Provider loading + caching
              └── models/*_provider.py
```

**Startup:** `load_config()` → `app_manager.initialize()` → `model_loader.initialize_models()` → `get_model_definitions()` (fetches from all 4 providers in parallel) → main loop.

**Request:** UI collects text → `ApplicationManager.process_text()` → `TaskProcessor.execute_task()` → formats prompt with `{user_text}` → invokes model `Callable[[str], str]` through a per-model `CircuitBreaker`.

Each provider implements `fetch_models()`, `get_fallback_models()`, and `build_callable(model_id, api_key) -> Callable[[str], str]`. Model keys use the format `"{provider}/{display_name}"` (e.g. `"anthropic/Claude Sonnet 4"`).

## Troubleshooting

### Configuration / missing API keys

```bash
python3 -m pytest tests/test_config_manager.py
```

Ensure at least one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, or `XAI_API_KEY` is set in `.env`.

### Dependencies

```bash
pip install -r requirements.txt
python3 -m pytest tests/
```

### Language detection

Auto-translation uses `langdetect`. If detection is wrong for short or mixed-language text, try longer samples or use the refine task instead.

## Quick Start

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Add at least one API key to `.env`
4. `python3 -m pytest tests/` to verify
5. `python3 main.py` to run
