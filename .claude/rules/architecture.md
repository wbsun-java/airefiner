---
description: Application architecture and layer separation
---

The application has a strict 4-layer separation:

```
main.py (AIRefinerApp)
  └── ui/console_interface.py      # All user I/O — no business logic
  └── core/app_manager.py          # ApplicationManager + TaskProcessor — no I/O
        └── models/model_loader.py # Orchestrates provider loading + caching
              └── models/*_provider.py  # One file per AI provider
```

**Startup flow:** `load_config()` → `app_manager.initialize()` → `model_loader.initialize_models()` → `get_model_definitions()` (fetches from all 5 providers in parallel via `ThreadPoolExecutor`) → main loop.

**Request flow:** UI collects text → `ApplicationManager.process_text()` → `TaskProcessor.execute_task()` → builds a LangChain chain (`ChatPromptTemplate | model | StrOutputParser`) → invoked through the model's `CircuitBreaker`.
