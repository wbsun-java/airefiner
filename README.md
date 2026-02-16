# AIRefiner

A professional AI-powered text processing tool designed to **refine, translate, and improve business communications**. Features clean architecture, dynamic model fetching from 5 AI providers, intelligent model filtering, and automatic language detection with smart task continuity.

## Program Objective

AIRefiner is a professional text processing tool that serves three main purposes:

1. **Text Refinement**: Transform informal text into professional, polished communications
2. **Presentation Enhancement**: Convert basic content into presentation-ready material with proper structure
3. **Intelligent Translation**: Automatic language detection with bidirectional English <-> Chinese translation

The program intelligently manages user workflow by offering previous result improvements only when continuing with the same task type.

## Core Features

### AI Provider Integration
- **Dynamic Model Fetching**: Real-time model discovery from 5 providers (OpenAI, Google, Anthropic, Groq, xAI)
- **Intelligent Filtering**: Excludes non-text model types (image, audio, video, embedding, code, moderation, safety models)
- **Provider-Specific Optimization**: Tailored fetching logic for each provider's API structure
- **Fallback System**: Graceful degradation when dynamic fetching fails

### Professional Architecture
- **Clean Separation**: UI layer -> Business logic -> Configuration -> Provider integration
- **State Management**: Intelligent tracking of selected models, tasks, and results
- **Circuit Breaker Pattern**: Prevents cascade failures in model execution
- **Error Recovery**: Comprehensive error handling with context-aware messages

### Smart Translation System
- **Automatic Detection**: Uses langdetect library for accurate language identification
- **Confidence Scoring**: Pattern-based confidence calculation for reliability
- **Fallback Logic**: Defaults to text refinement for unsupported languages
- **Bidirectional Support**: Chinese (Simplified/Traditional) <-> English

## Project Structure

```
airefiner/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── pytest.ini                 # Test configuration
├── .env                       # API keys (user-created, not in repo)
│
├── config/                    # Configuration management
│   ├── __init__.py
│   ├── constants.py           # Application constants, enums, filtering rules
│   └── config_manager.py      # Centralized configuration with validation
│
├── core/                      # Business logic layer
│   ├── __init__.py
│   └── app_manager.py         # Application state, task processing, workflow control
│
├── ui/                        # User interface layer
│   ├── __init__.py
│   └── console_interface.py   # Console UI with grouped model display
│
├── models/                    # AI model management
│   ├── __init__.py
│   ├── model_loader.py        # Orchestrator: filtering, caching, initialization
│   ├── base_model_provider.py # Abstract base class for model providers
│   ├── openai_provider.py     # OpenAI provider (GPT models)
│   ├── google_provider.py     # Google provider (Gemini models)
│   ├── anthropic_provider.py  # Anthropic provider (Claude models)
│   ├── groq_provider.py       # Groq provider (Llama, Mixtral, Gemma models)
│   └── xai_provider.py        # xAI/Grok provider with gRPC support
│
├── prompts/                   # Prompt templates
│   ├── __init__.py
│   ├── refine_prompts.py      # Text refinement and presentation prompts
│   └── translate_prompts.py   # Translation prompts (EN<->ZH)
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── input_helpers.py       # Multi-line input handling
│   ├── translation_handler.py # Language detection and auto-translation logic
│   ├── logger.py              # Structured console logging with color support
│   └── error_handler.py       # Error classes, circuit breaker, retry logic
│
├── tests/                     # Unit tests (pytest)
│   ├── __init__.py
│   ├── conftest.py            # Test fixtures and configuration
│   ├── test_app_manager.py    # Business logic tests
│   ├── test_config_manager.py # Configuration management tests
│   └── test_error_handler.py  # Error handling and circuit breaker tests
│
├── scripts/                   # Development and debugging utilities
│   ├── test_runner.py         # Run all integration scripts in sequence
│   ├── test_installation.py   # Verify dependencies are installed
│   ├── test_providers.py      # Test all AI provider connections
│   ├── test_auto_translation.py # Test auto-translation feature
│   ├── demo_dynamic_fetching.py # Demo dynamic model fetching
│   ├── debug_langdetect.py    # Debug language detection issues
│   └── check_langdetect_contents.py # Inspect langdetect package contents
│
└── docs/                      # Documentation
    ├── CONFIGURATION.md       # Setup and configuration guide
    └── PROJECT_STRUCTURE.md   # Detailed structure explanation
```

## Installation

### 1. Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Create `.env` file with your API keys:

```env
# Add keys ONLY for the services you have access to
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_xai_key_here
```

### 3. Verify installation:

```bash
python scripts/test_installation.py
```

## Usage

### Run the application:

```bash
python main.py
```

### Run all integration tests:

```bash
python scripts/test_runner.py
```

### Run specific tests:

```bash
# Unit tests (via pytest)
pytest tests/test_app_manager.py
pytest tests/test_config_manager.py
pytest tests/test_error_handler.py

# Integration scripts
python scripts/test_installation.py       # Verify dependencies
python scripts/test_providers.py          # Test all 5 AI provider connections
python scripts/test_auto_translation.py   # Test auto-translation feature
```

## Available Tasks

### 1. Text Refinement
Transform informal text into professional, polished communications (emails, messages, documents, articles).

### 2. Presentation Enhancement
Convert basic content into presentation-ready talking points with professional structure.

### 3. Intelligent Auto-Translation
Automatic language detection with intelligent translation direction:
- English detected -> Translate to Simplified Chinese
- Chinese detected -> Translate to English
- Other/Low confidence -> Fallback to Text Refinement

## Configuration

### API Keys

Set API keys via environment variables or a `.env` file in the project root. Only keys for services you use are required. See `docs/CONFIGURATION.md` for details.

### Model Filtering

The system automatically filters out non-text models (image, audio, video, embedding, code, moderation, etc.). Filtering rules are defined in `config/constants.py` under `ModelFiltering`.

### Logging

- Console-only logging (no log files)
- Color-coded output with Windows Unicode safety
- Log level configurable via `LOG_LEVEL` environment variable

## Architecture Overview

```
main.py (Entry Point)
├── ui/console_interface.py (UI Layer)
│   ├── MenuManager         - Menu display and user input
│   ├── ModelSelector        - Grouped model selection by provider
│   ├── TaskSelector         - Task selection with workflow management
│   └── InputHandler         - Multi-line input with task continuity
├── core/app_manager.py (Business Logic Layer)
│   ├── ApplicationManager   - Main coordinator and workflow control
│   ├── ModelManager          - Model lifecycle with circuit breakers
│   ├── TaskProcessor         - Task execution with error handling
│   └── AppState              - State tracking (model, task, results)
├── config/ (Configuration Layer)
│   ├── config_manager.py    - API keys, validation, environment loading
│   └── constants.py         - Enums, filtering rules, thresholds
├── models/ (Provider Integration Layer)
│   ├── model_loader.py      - Orchestrator: filtering, caching, initialization
│   ├── base_model_provider.py - Abstract base for providers
│   ├── openai_provider.py   - OpenAI GPT models
│   ├── google_provider.py   - Google Gemini models
│   ├── anthropic_provider.py - Anthropic Claude models
│   ├── groq_provider.py     - Groq Llama/Mixtral/Gemma models
│   └── xai_provider.py      - xAI gRPC + OpenAI-compat fallback
├── prompts/ (Prompt Engineering)
│   ├── refine_prompts.py    - Refinement and presentation templates
│   └── translate_prompts.py - EN<->ZH translation templates
└── utils/ (Utilities)
    ├── logger.py              - Singleton logger, console-only, color formatting
    ├── error_handler.py       - Custom exceptions, circuit breaker, retry
    ├── translation_handler.py - Language detection, confidence scoring
    └── input_helpers.py       - Multi-line input collection
```

## Troubleshooting

### Language Detection Issues:
```bash
python scripts/debug_langdetect.py
python scripts/check_langdetect_contents.py
```

### Missing Dependencies:
```bash
python scripts/test_installation.py
```

### Configuration Issues:
```bash
pytest tests/test_config_manager.py
```

## Quick Start

1. `pip install -r requirements.txt`
2. Add API keys to `.env` file
3. `python scripts/test_installation.py` to verify
4. `python main.py` to run
