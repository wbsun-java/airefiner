"""
Console user interface for AIRefiner application.
Separates UI logic from business logic.
"""

from typing import Dict, Any, Optional

from config.config_manager import get_config
from config.constants import UIConfig
from utils import input_helpers
from utils.logger import LoggerMixin


class MenuManager(LoggerMixin):
    """Manages console menu display and user input."""

    def display_menu(self, title: str, options: Dict[str, str],
                     exit_option_label: str = "Exit") -> str:
        """
        Display a numbered menu and get user choice.
        
        Args:
            title: Menu title
            options: Dictionary of option_key -> display_name
            exit_option_label: Label for exit option
            
        Returns:
            User's choice as string
        """
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print(f"--- {title} ---")
        print(UIConfig.MENU_SEPARATOR)

        for key, value in options.items():
            print(f"{key}. {value}")

        if exit_option_label:
            print(f"0. {exit_option_label}")

        print(UIConfig.MENU_SEPARATOR)
        return input("Enter choice: ").strip()

    def display_status_message(self, message: str, status_type: str = "info"):
        """
        Display a status message with appropriate prefix.
        
        Args:
            message: Message to display
            status_type: Type of status (success, error, warning, info)
        """
        prefix_map = {
            "success": UIConfig.SUCCESS_PREFIX,
            "error": UIConfig.ERROR_PREFIX,
            "warning": UIConfig.WARNING_PREFIX,
            "info": UIConfig.INFO_PREFIX,
            "loading": UIConfig.LOADING_PREFIX
        }

        prefix = prefix_map.get(status_type, UIConfig.INFO_PREFIX)
        print(f"{prefix} {message}")

    def display_result(self, result: str, title: str = "Result"):
        """
        Display processing result in a formatted way.
        
        Args:
            result: Result text to display
            title: Title for the result section
        """
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print(f"--- {title} ---")
        print(UIConfig.MENU_SEPARATOR)
        print(result)
        print(UIConfig.MENU_SEPARATOR)


class ModelSelector(LoggerMixin):
    """Handles model selection UI."""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager

    def select_model(self, available_models: list[str]) -> Optional[str]:
        """
        Handle model selection UI.
        
        Args:
            available_models: List of available model keys
            
        Returns:
            Selected model key, "exit" for exit, or None for invalid choice
        """
        if not available_models:
            self.menu_manager.display_status_message(
                "No models available for selection.", "error"
            )
            return None

        model_options = {str(i + 1): name for i, name in enumerate(available_models)}
        choice = self.menu_manager.display_menu("Select a Model", model_options)

        if choice == "0":
            return "exit"

        try:
            model_index = int(choice) - 1
            if 0 <= model_index < len(available_models):
                selected_model = available_models[model_index]
                self.menu_manager.display_status_message(
                    f"Selected model: {selected_model}", "success"
                )
                return selected_model
            else:
                self.menu_manager.display_status_message(
                    "Invalid choice. Please try again.", "error"
                )
                return None
        except ValueError:
            self.menu_manager.display_status_message(
                "Invalid choice. Please enter a number.", "error"
            )
            return None


class TaskSelector(LoggerMixin):
    """Handles task selection UI."""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager

    def select_task(self) -> Optional[Dict[str, Any]]:
        """
        Handle task selection UI.
        
        Returns:
            Selected task dictionary or None for back to previous menu
        """
        config = get_config()
        task_options = {key: info['name'] for key, info in config.tasks_config.tasks.items()}
        choice = self.menu_manager.display_menu(
            "Select a Task", task_options, "Back to model selection"
        )

        if choice == "0":
            return None

        selected_task = config.tasks_config.tasks.get(choice)
        if selected_task:
            self.menu_manager.display_status_message(
                f"Selected task: {selected_task['name']}", "success"
            )
        else:
            self.menu_manager.display_status_message(
                "Invalid task selection.", "error"
            )

        return selected_task


class InputHandler(LoggerMixin):
    """Handles user input collection."""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager

    def get_text_input(self, task_name: str, can_use_previous: bool = False,
                       previous_result: Optional[str] = None) -> Optional[str]:
        """
        Get text input from user.
        
        Args:
            task_name: Name of the current task
            can_use_previous: Whether previous result can be used
            previous_result: Previous result text
            
        Returns:
            User input text or None if cancelled
        """
        if can_use_previous and previous_result:
            choice = input("Refine the previous result? (y/n) [y]: ").strip().lower()
            if choice in ('y', ''):
                self.menu_manager.display_status_message(
                    "Using previous result as input", "info"
                )
                print("\n--- Previous Result ---")
                print(previous_result)
                print("----------------------")
                return previous_result

        prompt_msg = f"\nEnter the text for '{task_name}'"
        try:
            return input_helpers.get_multiline_input(prompt_msg)
        except KeyboardInterrupt:
            self.menu_manager.display_status_message(
                "Input cancelled by user.", "warning"
            )
            return None

    def get_refine_choice(self) -> bool:
        """
        Ask user if they want to refine further.
        
        Returns:
            True if user wants to refine further, False otherwise
        """
        print("\n--- Options ---")
        print("1. Refine this result further")
        print("2. Back to main menu")

        choice = input("Enter choice [2]: ").strip()
        return choice == "1"

    def get_save_choice(self) -> bool:
        """
        Ask user if they want to save the result.
        
        Returns:
            True if user wants to save, False otherwise
        """
        choice = input("Save result to file? (y/n) [n]: ").strip().lower()
        return choice == 'y'


class ConsoleInterface(LoggerMixin):
    """Main console interface coordinator."""

    def __init__(self):
        super().__init__()
        self.menu_manager = MenuManager()
        self.model_selector = ModelSelector(self.menu_manager)
        self.task_selector = TaskSelector(self.menu_manager)
        self.input_handler = InputHandler(self.menu_manager)

    def display_welcome_message(self):
        """Display welcome message."""
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("🤖 Welcome to AIRefiner")
        print("Your AI-powered text processing tool")
        print(f"{UIConfig.MENU_SEPARATOR}")

    def display_goodbye_message(self):
        """Display goodbye message."""
        print(f"\n{UIConfig.MENU_SEPARATOR}")
        print("👋 Thank you for using AIRefiner!")
        print("Goodbye!")
        print(f"{UIConfig.MENU_SEPARATOR}")

    def select_model(self, available_models: list[str]) -> Optional[str]:
        """Select a model through the UI."""
        return self.model_selector.select_model(available_models)

    def select_task(self) -> Optional[Dict[str, Any]]:
        """Select a task through the UI."""
        return self.task_selector.select_task()

    def get_text_input(self, task_name: str, can_use_previous: bool = False,
                       previous_result: Optional[str] = None) -> Optional[str]:
        """Get text input through the UI."""
        return self.input_handler.get_text_input(task_name, can_use_previous, previous_result)

    def display_result(self, result: str):
        """Display processing result."""
        self.menu_manager.display_result(result)

    def get_refine_choice(self) -> bool:
        """Get user choice for further refinement."""
        return self.input_handler.get_refine_choice()

    def get_save_choice(self) -> bool:
        """Get user choice for saving result."""
        return self.input_handler.get_save_choice()

    def display_status(self, message: str, status_type: str = "info"):
        """Display a status message."""
        self.menu_manager.display_status_message(message, status_type)

    def display_error(self, message: str):
        """Display an error message."""
        self.menu_manager.display_status_message(message, "error")

    def display_success(self, message: str):
        """Display a success message."""
        self.menu_manager.display_status_message(message, "success")

    def display_warning(self, message: str):
        """Display a warning message."""
        self.menu_manager.display_status_message(message, "warning")
