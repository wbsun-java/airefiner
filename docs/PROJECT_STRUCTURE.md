# Project Structure

## 📁 Organized Directory Layout

```
airefiner/
├── 📁 config/              # Configuration files
│   ├── __init__.py
│   └── settings.py         # API keys, tasks, filtering settings
│
├── 📁 models/              # Model loading and management
│   ├── __init__.py
│   ├── model_loader.py     # ⭐ Dynamic model fetching with intelligent filtering
│   └── custom_model.py     # Custom model implementations
│
├── 📁 prompts/             # Prompt templates
│   ├── __init__.py
│   ├── refine_prompts.py   # Text refinement prompts
│   └── translate_prompts.py # Translation prompts
│
├── 📁 utils/               # Utility functions
│   ├── __init__.py
│   └── input_helpers.py    # Input handling utilities
│
├── 📁 tests/               # 🧪 All test files (organized)
│   ├── __init__.py
│   ├── test_installation.py          # Verify dependencies
│   ├── test_filtering_simple.py      # Basic filtering tests
│   ├── test_comprehensive_filtering.py # Complete filtering test suite
│   ├── test_actual_filtering.py      # Real function tests
│   ├── test_model_filtering.py       # Model filtering validation
│   ├── test_anthropic.py             # Anthropic provider tests
│   ├── test_gemini.py                # Google Gemini tests
│   ├── test_groq.py                  # Groq provider tests
│   └── test_models.py                # General model tests
│
├── 📁 scripts/             # 🔧 Utility scripts
│   ├── test_runner.py      # ⭐ Run all tests in sequence
│   ├── demo_dynamic_fetching.py # Demo dynamic fetching
│   └── run_test.py         # Individual test runner
│
├── 📁 docs/                # 📖 Documentation
│   ├── PROJECT_STRUCTURE.md # This file
│   └── CONFIGURATION.md    # Configuration guide
│
├── 📄 main.py              # 🚀 Main application entry point
├── 📄 requirements.txt     # 📦 Dependencies
├── 📄 README.md           # 📋 Project overview
└── 📄 .env               # 🔐 API keys (not in repo)
```

## 🎯 Key Features Location

### Core Functionality:

- **Dynamic Model Fetching**: `models/model_loader.py:58-331`
- **Intelligent Filtering**: `models/model_loader.py:54-116`
- **Main Application**: `main.py`
- **Configuration**: `config/settings.py`

### Testing:

- **Quick Test**: `python scripts/test_runner.py`
- **Installation Test**: `python tests/test_installation.py`
- **Filtering Test**: `python tests/test_comprehensive_filtering.py`

### Documentation:

- **Setup Guide**: `README.md`
- **Configuration**: `docs/CONFIGURATION.md`
- **Structure**: `docs/PROJECT_STRUCTURE.md`

## 🧹 Clean Root Directory

The root directory now only contains:

- Essential application files (`main.py`, `requirements.txt`)
- Documentation (`README.md`)
- Configuration (`.env`)
- Organized folders for specific purposes

All test files are properly organized in `tests/` and utility scripts in `scripts/`.