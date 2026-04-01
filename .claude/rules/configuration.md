---
description: Configuration and API key setup
---

API keys are loaded from `.env` via `python-dotenv`. Supported variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`. At least one must be set.

`config/config_manager.py` holds the `TASKS` dict (maps menu numbers `"1"–"3"` to task dicts). This must stay in sync with `TaskConfiguration` constants in `config/constants.py`.
