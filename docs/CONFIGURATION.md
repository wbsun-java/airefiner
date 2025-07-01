# Configuration Guide

## Environment Variables (.env)

Create a `.env` file in the root directory with your API keys:

```env
# Add keys ONLY for the services you have access to
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_xai_key_here
```

## Settings Configuration (config/settings.py)

### Model Filtering

```python
# Enable/disable strict filtering of non-text models
ENABLE_STRICT_MODEL_FILTERING = True

# Additional keywords to exclude (case-insensitive)
CUSTOM_EXCLUDE_KEYWORDS = [
    # Add any custom keywords you want to exclude
    # 'keyword1', 'keyword2'
]
```

### Task Definitions

```python
TASKS = {
    "1": {"id": "refine", "name": "Refine Text (Email, Article, etc.)"},
    "2": {"id": "refine_presentation", "name": "Refine Presentation (Summarize Article)"},
    "3": {"id": "en_to_zh", "name": "Translate: English -> Chinese"},
    "4": {"id": "zh_to_en", "name": "Translate: Chinese -> English"},
}
```

## Model Filtering Details

The system automatically filters out models that are not suitable for text refinement:

### Excluded Model Types:

- **Image/Vision**: dalle, vision, image, visual, pic, photo
- **Audio**: whisper, tts, speech, voice, sound, music
- **Video**: video, motion, animation
- **Embedding**: embed, embedding, vector, similarity
- **Code**: code, programming, dev, developer
- **Moderation**: moderation, safety, content-filter, toxic
- **Guard/Security**: guard, guardian, safety-model
- **Legacy/Edit**: edit, davinci-edit, curie-edit
- **Specialized**: reasoning, math, science, research

### Included Model Types:

Models with these indicators are included:

- chat, gpt, claude, gemini, llama, mistral, qwen, deepseek, grok
- text, language, conversation, instruct, assistant

## Caching

- Model definitions are cached for 1 hour to reduce API calls
- Cache is automatically refreshed when expired
- No manual cache management needed