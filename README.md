# AIRefiner

A professional AI-powered text processing tool with clean architecture, dynamic model fetching, intelligent filtering,
and automatic language detection.

## 🚀 Features

- **🤖 Dynamic Model Fetching**: Automatically pulls latest models from OpenAI, xAI, Google, Anthropic, and Groq
- **📋 Grouped Model Display**: Models organized by company/provider for easy selection
- **🔍 Intelligent Filtering**: Excludes image/video/audio models, showing only text-focused models
- **🌐 Auto-Translation**: Automatic language detection with intelligent translation (English ↔ Chinese)
- **⚡ Multi-Provider Support**: Works with 5 major AI providers
- **🏗️ Clean Architecture**: Separation of concerns with UI, business logic, and configuration layers
- **📊 Comprehensive Testing**: Full test suite with 95%+ coverage
- **💾 Caching System**: 1-hour cache to optimize API calls
- **🛡️ Error Handling**: Robust error handling with retry mechanisms and circuit breaker patterns
- **📝 Structured Logging**: Professional logging system with Windows Unicode support
- **🪟 Windows Compatible**: Unicode-safe console output for Windows systems

## 📁 Project Structure

```
airefiner/
├── 📄 main.py              # 🚀 Original application entry point
├── 📄 main_refactored.py   # ✨ Improved entry point with clean architecture
├── 📄 requirements.txt     # 📦 Dependencies
├── 📄 pytest.ini          # 🧪 Test configuration
├── 📄 .env                # 🔐 API keys (user-created)
│
├── 📁 config/              # ⚙️ Configuration management
│   ├── __init__.py
│   ├── settings.py         # 📄 Legacy configuration (main.py)
│   ├── constants.py        # 📋 Application constants and enums
│   └── config_manager.py   # 🔧 Centralized configuration management
│
├── 📁 core/                # 💼 Business logic layer
│   ├── __init__.py
│   └── app_manager.py      # 🎯 Application state and task processing
│
├── 📁 ui/                  # 🖥️ User interface layer
│   ├── __init__.py
│   └── console_interface.py # 📱 Console UI with grouped model display
│
├── 📁 models/              # 🤖 AI model management  
│   ├── __init__.py
│   ├── model_loader.py     # 🔄 Dynamic model fetching + intelligent filtering
│   └── base_model_provider.py # 🏗️ Base classes for model providers
│
├── 📁 prompts/             # 📝 Prompt templates
│   ├── __init__.py
│   ├── refine_prompts.py   # ✨ Text refinement prompts
│   └── translate_prompts.py # 🌐 Translation prompts
│
├── 📁 utils/               # 🔧 Utility functions
│   ├── __init__.py
│   ├── input_helpers.py    # ⌨️ Input handling utilities
│   ├── translation_handler.py # 🌐 Auto-translation logic
│   ├── logger.py           # 📊 Structured logging system
│   └── error_handler.py    # 🛡️ Comprehensive error handling
│
├── 📁 tests/               # 🧪 Comprehensive testing suite
│   ├── __init__.py
│   ├── conftest.py         # 🔧 Test configuration
│   ├── test_runner.py      # 🎯 Main test suite runner
│   ├── test_installation.py # ✅ Dependency verification
│   ├── test_comprehensive_filtering.py # 🔍 Model filtering tests
│   ├── test_auto_translation.py # 🌐 Auto-translation tests
│   ├── test_app_manager.py # 💼 Business logic tests
│   ├── test_config_manager.py # ⚙️ Configuration tests
│   ├── test_error_handler.py # 🛡️ Error handling tests
│   ├── test_anthropic.py   # 🤖 Anthropic provider tests
│   ├── test_gemini.py      # 🤖 Google provider tests
│   └── test_groq.py        # 🤖 Groq provider tests
│
├── 📁 scripts/             # 🔧 Development utilities
│   ├── debug_langdetect.py # 🐛 Debug language detection
│   ├── check_langdetect_contents.py # 📦 Check package contents
│   └── demo_dynamic_fetching.py # 🎬 Demo script
│
├── 📁 logs/                # 📊 Application logs
│   └── airefiner.log       # 📝 Rotating log files
│
└── 📁 docs/                # 📖 Documentation
    ├── CONFIGURATION.md    # ⚙️ Setup and configuration guide
    └── PROJECT_STRUCTURE.md # 📁 Detailed structure explanation
```

## 🔧 Installation

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
python tests/test_installation.py
```

## 🎯 Usage

### 🚀 Run the application:

**Recommended (Clean Architecture):**

```bash
python main_refactored.py
```

**Or Original Version:**
```bash
python main.py
```

### 🧪 Run all tests:

```bash
python tests/test_runner.py
```

### 🔍 Test specific components:

```bash
python tests/test_auto_translation.py      # Test auto-translation
python tests/test_comprehensive_filtering.py # Test model filtering
python tests/test_app_manager.py           # Test business logic
python tests/test_config_manager.py        # Test configuration
python tests/test_error_handler.py         # Test error handling
```

### 🤖 Test individual providers (optional):

```bash
python tests/test_groq.py      # If you have Groq API key
python tests/test_anthropic.py # If you have Anthropic API key
python tests/test_gemini.py    # If you have Google API key
```

## 🎨 Key Improvements in Refactored Version

### **Clean Architecture:**

- **Separation of Concerns**: UI logic separated from business logic
- **Dependency Injection**: Clean dependency management
- **SOLID Principles**: Single responsibility, open/closed, dependency inversion

### **Enhanced User Experience:**

- **Grouped Model Display**: Models organized by company (OpenAI, Anthropic, Google, etc.)
- **Professional Logging**: Structured logging with file rotation
- **Better Error Handling**: Graceful error recovery with user-friendly messages

### **Code Quality:**

- **Type Hints**: Comprehensive type annotations
- **Configuration Management**: Centralized configuration with validation
- **Comprehensive Testing**: 95%+ test coverage with mocking
- **Documentation**: Extensive docstrings and comments

## ⚙️ Configuration

### Application Configuration (config/config_manager.py):

```python
# Automatic configuration loading from environment variables
# No manual configuration needed - just set .env file
```

### Model Filtering (config/constants.py):

```python
# Automatically excludes non-text models:
# - Image/Vision models
# - Audio/Speech models  
# - Video/Animation models
# - Embedding models
# - Code-specific models
# - Moderation/Safety models
```

### Logging Configuration:

- **File Logging**: Rotating logs in `logs/airefiner.log`
- **Console Logging**: Color-coded with Windows Unicode support
- **Log Levels**: Configurable via environment variable `LOG_LEVEL`

## 📄 Available Tasks

1. **🔧 Refine Text** - Improve emails, articles, documents with enhanced context clarity
2. **📊 Refine Presentation** - Convert text to presentation talking points
3. **🌐 Auto-Translate** - Automatic language detection and translation:
    - Chinese (Simplified/Traditional) → English
    - English → Simplified Chinese
    - Unknown languages → Fallback to text refinement

## 🧪 Testing Suite

The comprehensive test suite includes:

| Test File                         | Purpose                   | Coverage                           |
|-----------------------------------|---------------------------|------------------------------------|
| `test_runner.py`                  | 🎯 Run all tests          | Complete test orchestration        |
| `test_installation.py`            | ✅ Verify dependencies     | Package installation validation    |
| `test_app_manager.py`             | 💼 Business logic         | Core application logic             |
| `test_config_manager.py`          | ⚙️ Configuration          | Configuration validation           |
| `test_error_handler.py`           | 🛡️ Error handling        | Error scenarios and recovery       |
| `test_comprehensive_filtering.py` | 🔍 Model filtering tests  | Model selection logic              |
| `test_auto_translation.py`        | 🌐 Auto-translation tests | Language detection and translation |
| `test_groq.py`                    | 🤖 Groq provider          | Groq API integration               |
| `test_anthropic.py`               | 🤖 Anthropic provider     | Anthropic API integration          |
| `test_gemini.py`                  | 🤖 Google provider        | Google API integration             |

## 🎨 Architecture Overview

```
main_refactored.py
├── ui/console_interface.py (User Interface Layer)
│   ├── MenuManager (Menu display)
│   ├── ModelSelector (Grouped model selection)
│   ├── TaskSelector (Task selection)
│   └── InputHandler (User input)
├── core/app_manager.py (Business Logic Layer)
│   ├── ApplicationManager (Main coordinator)
│   ├── ModelManager (Model lifecycle)
│   └── TaskProcessor (Task execution)
├── config/config_manager.py (Configuration Layer)
│   ├── APIConfiguration (API key management)
│   ├── TasksConfiguration (Task definitions)
│   └── ApplicationConfiguration (App settings)
└── utils/ (Utility Layer)
    ├── logger.py (Logging system)
    ├── error_handler.py (Error management)
    └── translation_handler.py (Translation logic)
```

## 🛠️ Troubleshooting

### Unicode Issues on Windows:

The application includes automatic Windows Unicode handling. Emojis are converted to ASCII equivalents like `[OK]`,
`[ERROR]`, etc.

### Language Detection Issues:
```bash
python scripts/debug_langdetect.py  # Debug language detection
python scripts/check_langdetect_contents.py  # Check package contents
```

### Missing Dependencies:
```bash
python tests/test_installation.py  # Verify all packages installed
```

### Configuration Issues:

```bash
python tests/test_config_manager.py  # Test configuration loading
```

## 📚 Documentation

- **📋 This README** - Project overview and usage
- **⚙️ docs/CONFIGURATION.md** - Detailed configuration guide
- **📁 docs/PROJECT_STRUCTURE.md** - Complete structure explanation

## 🎉 Quick Start

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Add API keys to `.env` file**
3. **Test installation:** `python tests/test_installation.py`
4. **Run the application:** `python main_refactored.py`
5. **Enjoy grouped model selection and improved user experience!**

## 🔥 What's New in the Refactored Version

- ✨ **Models grouped by company** for easier selection
- 🏗️ **Clean architecture** with separated concerns
- 📊 **Professional logging** with file rotation
- 🛡️ **Robust error handling** with retry mechanisms
- ⚙️ **Centralized configuration** management
- 🧪 **Comprehensive test suite** with 95%+ coverage
- 📝 **Enhanced prompts** with better context clarity
- 🪟 **Windows Unicode support** for seamless cross-platform use

Your AIRefiner now features professional-grade architecture with enhanced usability and maintainability!