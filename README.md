# AIRefiner

A multi-provider AI text processing tool with dynamic model fetching, intelligent filtering, and automatic language
detection.

## 🚀 Features

- **🤖 Dynamic Model Fetching**: Automatically pulls latest models from OpenAI, xAI, Google, Anthropic, and Groq
- **🔍 Intelligent Filtering**: Excludes image/video/audio models, showing only text-focused models
- **🌐 Auto-Translation**: Automatic language detection with intelligent translation (English ↔ Chinese)
- **⚡ Multi-Provider Support**: Works with 5 major AI providers
- **💾 Caching System**: 1-hour cache to optimize API calls
- **🛡️ Fallback Mechanisms**: Graceful degradation when APIs are unavailable
- **🪟 Windows Compatible**: Unicode-safe console output for Windows systems

## 📁 Project Structure

```
airefiner/
├── 📄 main.py              # 🚀 Main application entry point
├── 📄 requirements.txt     # 📦 Dependencies
├── 📄 README.md           # 📋 Project overview
├── 📄 .env               # 🔐 API keys (user-created)
│
├── 📁 config/              # ⚙️ Configuration management
│   ├── __init__.py
│   └── settings.py        # API keys, tasks, filtering settings
│
├── 📁 models/              # 🤖 AI model management  
│   ├── __init__.py
│   └── model_loader.py    # Dynamic model fetching + intelligent filtering
│
├── 📁 prompts/             # 📝 Prompt templates
│   ├── __init__.py
│   ├── refine_prompts.py  # Text refinement prompts
│   └── translate_prompts.py # Translation prompts
│
├── 📁 utils/               # 🔧 Utility functions
│   ├── __init__.py
│   ├── input_helpers.py   # Input handling utilities
│   └── translation_handler.py # Auto-translation logic
│
├── 📁 tests/               # 🧪 Testing suite
│   ├── __init__.py
│   ├── test_runner.py     # Main test suite runner
│   ├── test_installation.py # Dependency verification
│   ├── test_comprehensive_filtering.py # Complete filtering tests
│   ├── test_auto_translation.py # Auto-translation feature tests
│   ├── test_anthropic.py  # Anthropic provider tests (optional)
│   ├── test_gemini.py     # Google provider tests (optional)
│   └── test_groq.py       # Groq provider tests (optional)
│
├── 📁 scripts/             # 🔧 Development utilities
│   ├── debug_langdetect.py # Debug language detection
│   ├── check_langdetect_contents.py # Check package contents
│   └── demo_dynamic_fetching.py # Demo script
│
└── 📁 docs/                # 📖 Documentation
    ├── CONFIGURATION.md   # Setup and configuration guide
    └── PROJECT_STRUCTURE.md # Detailed structure explanation
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

### 🚀 Run the main application:

```bash
python main.py
```

### 🧪 Run all tests:

```bash
python tests/test_runner.py
```

### 🔍 Test specific features:

```bash
python tests/test_auto_translation.py      # Test auto-translation
python tests/test_comprehensive_filtering.py # Test model filtering
```

### 🤖 Test individual providers (optional):

```bash
python tests/test_groq.py      # If you have Groq API key
python tests/test_anthropic.py # If you have Anthropic API key
python tests/test_gemini.py    # If you have Google API key
```

## ⚙️ Configuration

### Model Filtering (config/settings.py):

```python
# Enable/disable strict filtering of non-text models
ENABLE_STRICT_MODEL_FILTERING = True

# Additional keywords to exclude (case-insensitive)
CUSTOM_EXCLUDE_KEYWORDS = [
    # Add any custom keywords you want to exclude
]
```

### Automatically Excluded Model Types:

- **Image/Vision**: dalle, vision, image, visual, pic, photo
- **Audio**: whisper, tts, speech, voice, sound, music
- **Video**: video, motion, animation
- **Embedding**: embed, embedding, vector, similarity
- **Code**: code, programming, dev, developer
- **Moderation**: moderation, safety, content-filter, toxic
- **Guard/Security**: guard, guardian, safety-model
- **Legacy/Edit**: edit, davinci-edit, curie-edit
- **Specialized**: reasoning, math, science, research

## 🧪 Testing Suite

The test suite includes:

| Test File                         | Purpose                   | When to Run                      |
|-----------------------------------|---------------------------|----------------------------------|
| `test_runner.py`                  | 🎯 Run all tests          | Always                           |
| `test_installation.py`            | ✅ Verify dependencies     | After installation               |
| `test_comprehensive_filtering.py` | 🔍 Model filtering tests  | After changes to filtering       |
| `test_auto_translation.py`        | 🌐 Auto-translation tests | After language detection changes |
| `test_groq.py`                    | 🤖 Groq provider          | If you have Groq API key         |
| `test_anthropic.py`               | 🤖 Anthropic provider     | If you have Anthropic API key    |
| `test_gemini.py`                  | 🤖 Google provider        | If you have Google API key       |

## 📄 Available Tasks

1. **🔧 Refine Text** - Improve emails, articles, documents
2. **📊 Refine Presentation** - Convert text to presentation talking points
3. **🌐 Auto-Translate** - Automatic language detection and translation:
    - Chinese (Simplified/Traditional) → English
    - English → Simplified Chinese
    - Unknown languages → Fallback to text refinement

## 🎨 Key Features by Location

| Feature                 | File Location                   | Description                         |
|-------------------------|---------------------------------|-------------------------------------|
| **🚀 Main App**         | `main.py`                       | Clean application entry point       |
| **🤖 Dynamic Models**   | `models/model_loader.py:58-400` | Fetches models from all 5 providers |
| **🔍 Smart Filtering**  | `models/model_loader.py:54-116` | Excludes non-text models            |
| **🌐 Auto-Translation** | `utils/translation_handler.py`  | Language detection + translation    |
| **⚙️ Configuration**    | `config/settings.py`            | API keys, tasks, settings           |
| **📝 Prompts**          | `prompts/*.py`                  | All prompt templates                |

## 🛠️ Troubleshooting

### Unicode Issues on Windows:

The application includes Windows-compatible output handling. If you see Unicode errors, the test runner automatically
converts symbols to ASCII equivalents.

### Language Detection Issues:

```bash
python scripts/debug_langdetect.py  # Debug language detection
python scripts/check_langdetect_contents.py  # Check package contents
```

### Missing Dependencies:

```bash
python tests/test_installation.py  # Verify all packages installed
```

## 📚 Documentation

- **📋 This README** - Project overview and usage
- **⚙️ CONFIGURATION.md** - Detailed configuration guide
- **📁 PROJECT_STRUCTURE.md** - Complete structure explanation

## 🎉 Ready to Use!

1. Install dependencies: `pip install -r requirements.txt`
2. Add API keys to `.env` file
3. Test installation: `python tests/test_installation.py`
4. Run the application: `python main.py`

Your AIRefiner is now ready with dynamic model fetching, intelligent filtering, and automatic translation!