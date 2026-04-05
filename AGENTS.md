# Repository Guidelines

## Project Purpose
AIRefiner is a console-based text processing tool for business communication workflows. It refines informal writing, reshapes content into presentation-ready material, and performs English/Chinese translation using multiple AI providers behind a shared application layer.

## Project Structure & Module Organization
`main.py` is the CLI entry point. Keep user interaction in `ui/`, business flow in `core/`, provider loading and filtering in `models/`, configuration in `config/`, prompt templates in `prompts/`, and shared helpers in `utils/`. Put tests in `tests/` and longer-form design notes in `docs/`.

```text
.
├── main.py          # CLI entry point
├── config/          # Constants and configuration loading
├── core/            # Application orchestration and task execution
├── models/          # Provider adapters, model loading, filtering
├── prompts/         # Prompt templates for refine/translate tasks
├── ui/              # Console interaction layer
├── utils/           # Logging, errors, helpers, translation support
├── tests/           # Pytest unit tests
└── docs/            # Additional design and workflow notes
```

Follow the existing layer boundaries: UI should not hold business logic, and provider-specific behavior belongs in `models/*_provider.py`.

## Build, Test, and Development Commands
Set up a local environment with `python3 -m venv .venv` and `source .venv/bin/activate`, then install dependencies with `pip install -r requirements.txt`.

- `python3 main.py`: run the console app locally.
- `python3 -m pytest tests/`: run the full unit test suite.
- `python3 -m pytest tests/test_app_manager.py`: run one test file.
- `python3 -m pytest tests/test_app_manager.py::TestTaskProcessor::test_execute_task_success`: run one focused test.

Use real API keys in `.env` only when intentionally exercising live providers.

## Coding Style & Naming Conventions
Use 4-space indentation and keep modules focused. Match the current Python style: `snake_case` for functions and variables, `CapWords` for classes, and short descriptive docstrings on public classes and fixtures. Prefer explicit imports and typed signatures where the surrounding code already uses them. Keep task IDs and provider names sourced from constants rather than hard-coded strings.

No formatter or linter config is committed today, so preserve the existing formatting and avoid introducing new tooling without discussion.

## Testing Guidelines
Testing uses `pytest` with discovery configured in `pytest.ini`. Name files `test_*.py`, classes `Test*`, and functions `test_*`. Default to unit tests; mark slower or live-provider coverage with existing markers such as `integration`, `slow`, and `api`. Add or update tests alongside behavior changes, especially around `ApplicationManager`, provider loading, and error-handling paths.

## Commit & Pull Request Guidelines
Recent history follows concise, prefix-based subjects such as `docs: ...`, `test: ...`, and `refactor: ...`. Keep commits narrowly scoped and written in imperative mood.

PRs should explain the behavior change, list the commands you ran, and note any config or API-key impact. Include terminal output snippets or screenshots only when a CLI flow or user-visible messaging changed.
