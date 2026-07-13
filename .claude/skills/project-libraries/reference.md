# Project Library Reference

Pinned version floors (from requirements.txt): anthropic>=0.86, openai>=2.30, google-genai>=1.69, groq>=1.1, xai-sdk>=1.11

---

## anthropic

```python
import anthropic
client = anthropic.Anthropic(api_key="...")

# Model listing
page = client.models.list()
for model in page.data:
    model.id           # e.g. "claude-sonnet-4-20250514"
    model.display_name # e.g. "Claude Sonnet 4"

# Inference
msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    temperature=0.7,
    messages=[{"role": "user", "content": "..."}],
)
text = msg.content[0].text
```

---

## openai

```python
from openai import OpenAI
client = OpenAI(api_key="...")

# Model listing
models = client.models.list()
for m in models.data:
    m.id  # e.g. "gpt-4o"

# Inference
completion = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.7,
    messages=[{"role": "user", "content": "..."}],
)
text = completion.choices[0].message.content
```

---

## groq

Identical interface to openai above. Swap client:

```python
from groq import Groq
client = Groq(api_key="...")

# Model listing
models = client.models.list()
for m in models.data:
    m.id  # e.g. "llama-3.1-70b-versatile"

# Inference — same as openai chat completions
completion = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    temperature=0.7,
    messages=[{"role": "user", "content": "..."}],
)
text = completion.choices[0].message.content
```

---

## google-genai

```python
from google import genai
client = genai.Client(api_key="...")

# Model listing
models = list(client.models.list())
for model in models:
    name = model.name.split('/')[-1]  # strip "models/" prefix
    model.supported_actions            # list; check for 'generateContent'

# Inference
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="...",
    config=genai.types.GenerateContentConfig(temperature=0.7),
)
text = response.text
```

---

## xai-sdk

Different pattern from the others — uses a chat builder, not a single call.

```python
from xai_sdk import Client
from xai_sdk.chat import user as xai_user

client = Client(api_key="...")

# Model listing
language_models = client.models.list_language_models()
for m in language_models:
    m.name  # e.g. "grok-3"

# Inference
chat = client.chat.create(model="grok-3")
chat.append(xai_user("..."))
response = chat.sample()
text = response.content
```

---

## Trivial packages (no reference needed)

- **python-dotenv**: `from dotenv import load_dotenv; load_dotenv()`
- **requests**: standard HTTP — rely on training knowledge
- **langdetect**: `from langdetect import detect; lang = detect(text)` → ISO 639-1 code
