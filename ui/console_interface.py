"""
Console user interface for AIRefiner application.
"""

from typing import Dict, Any, Optional, List

from config.constants import UIConfig
from models.model_filter import natural_sort_key
from utils import input_helpers
from utils.logger import LoggerMixin


class ConsoleInterface(LoggerMixin):
    """Console interface for model/task selection, text input, and result display."""

    def display_welcome_message(self):
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("🤖 Welcome to AIRefiner")
        print("Your AI-powered text processing tool")
        print(UIConfig.MENU_SEPARATOR)

    def display_goodbye_message(self):
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("👋 Thank you for using AIRefiner!")
        print("Goodbye!")
        print(UIConfig.MENU_SEPARATOR)

    def display_status(self, message: str, status_type: str = "info"):
        prefix_map = {
            "success": UIConfig.SUCCESS_PREFIX,
            "error": UIConfig.ERROR_PREFIX,
            "warning": UIConfig.WARNING_PREFIX,
            "info": UIConfig.INFO_PREFIX,
            "loading": UIConfig.LOADING_PREFIX,
        }
        print(f"{prefix_map.get(status_type, UIConfig.INFO_PREFIX)} {message}")

    def display_error(self, message: str):
        self.display_status(message, "error")

    def display_warning(self, message: str):
        self.display_status(message, "warning")

    def display_result(self, result: str, title: str = "Result"):
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print(f"--- {title} ---")
        print(UIConfig.MENU_SEPARATOR)
        print(result)
        print(UIConfig.MENU_SEPARATOR)

    # ── Model selection ──────────────────────────────────────────────

    def select_model(self, available_models: List[str]) -> Optional[str]:
        if not available_models:
            self.display_status("No models available for selection.", "error")
            return None

        grouped = self._group_models_by_provider(available_models)

        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("--- Select a Model ---")
        print(UIConfig.MENU_SEPARATOR)

        counter = 1
        model_mapping = {}
        for provider, models in grouped.items():
            print(f"\n📋 {provider} Models:")
            print("-" * (len(provider) + 9))
            for model_key, model_name in models:
                print(f"{counter}. {model_name}")
                model_mapping[str(counter)] = model_key
                counter += 1

        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("0. Exit")
        print(UIConfig.MENU_SEPARATOR)

        choice = input("Enter choice: ").strip()

        if choice == "0":
            return "exit"
        if choice in model_mapping:
            selected = model_mapping[choice]
            self.display_status(f"Selected model: {selected}", "success")
            return selected
        self.display_status("Invalid choice. Please try again.", "error")
        return None

    def _group_models_by_provider(self, available_models: List[str]) -> Dict[str, List[tuple]]:
        grouped: Dict[str, List[tuple]] = {}
        _display_names = {"xai": "xAI"}

        for model in available_models:
            if "/" in model:
                provider = model.split("/")[0]
                model_name = model.split("/", 1)[1]
            else:
                provider = "Unknown"
                model_name = model

            provider_display = _display_names.get(provider.lower(), provider.capitalize())
            grouped.setdefault(provider_display, []).append((model, model_name))

        return {p: sorted(models, key=lambda x: natural_sort_key(x[1]))
                for p, models in sorted(grouped.items())}

    # ── Task selection ───────────────────────────────────────────────

    def select_task(self, tasks: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        task_options = {key: info['name'] for key, info in tasks.items()}

        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("--- Select a Task ---")
        print(UIConfig.MENU_SEPARATOR)
        for key, value in task_options.items():
            print(f"{key}. {value}")
        print("0. Back to model selection")
        print(UIConfig.MENU_SEPARATOR)

        choice = input("Enter choice: ").strip()

        if choice == "0":
            return None

        selected_task = tasks.get(choice)
        if selected_task:
            self.display_status(f"Selected task: {selected_task['name']}", "success")
        else:
            self.display_status("Invalid task selection.", "error")
        return selected_task

    # ── Text input ───────────────────────────────────────────────────

    def get_text_input(self, task_name: str, can_use_previous: bool = False,
                       previous_result: Optional[str] = None) -> Optional[str]:
        if can_use_previous and previous_result:
            choice = input("Improve the previous result? (y/n) [y]: ").strip().lower()
            if choice in ('y', ''):
                self.display_status("Using previous result as input for further improvement", "info")
                print("\n--- Previous Result ---")
                print(previous_result)
                print("----------------------")
                return previous_result

        try:
            return input_helpers.get_multiline_input(f"\nEnter the text for '{task_name}'")
        except KeyboardInterrupt:
            self.display_status("Input cancelled by user.", "warning")
            return None

    def get_refine_choice(self) -> bool:
        print("\n--- Options ---")
        print("1. Improve this result further")
        print("2. Back to main menu")
        return input("Enter choice [2]: ").strip() == "1"
