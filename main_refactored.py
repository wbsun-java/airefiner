"""
Refactored main application entry point for AIRefiner.
Demonstrates improved separation of concerns with business logic and UI logic.
"""

from dotenv import load_dotenv

# Load environment variables from .env file before other imports
load_dotenv()

from core.app_manager import ApplicationManager
from ui.console_interface import ConsoleInterface
from utils.logger import LoggerMixin
from config.config_manager import load_config


class AIRefinerApp(LoggerMixin):
    """Main application class that coordinates UI and business logic."""

    def __init__(self):
        super().__init__()
        self.app_manager = ApplicationManager()
        self.ui = ConsoleInterface()

    def run(self):
        """Run the main application loop."""
        try:
            self.logger.info("Starting AIRefiner application")
            self.ui.display_welcome_message()

            # Load and validate configuration
            load_config()

            # Initialize the application
            self.app_manager.initialize()

            # Main interaction loop
            self._main_loop()

        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            self.ui.display_warning("Application interrupted by user")
        except Exception as e:
            self.logger.exception(f"Unexpected error in main application: {e}")
            self.ui.display_error(f"Unexpected error: {e}")
        finally:
            self.ui.display_goodbye_message()
            self.logger.info("AIRefiner application terminated")

    def _main_loop(self):
        """Main application interaction loop."""
        while not self.app_manager.should_exit():
            try:
                # Model selection
                if not self.app_manager.app_state.selected_model:
                    model_choice = self._handle_model_selection()
                    if model_choice == "exit":
                        self.app_manager.exit_application()
                        break
                    elif model_choice is None:
                        continue  # Invalid choice, try again

                    self.app_manager.set_selected_model(model_choice)

                # Task selection
                if not self.app_manager.app_state.selected_task:
                    task_choice = self.ui.select_task()
                    if task_choice is None:
                        # User chose to go back to model selection
                        self.app_manager.reset_model_selection()
                        continue

                    self.app_manager.set_selected_task(task_choice)

                # Text input and processing
                self._handle_text_processing()

                # Post-processing options
                if not self._handle_post_processing():
                    # User chose to go back to main menu
                    self.app_manager.reset_model_selection()
                    self.app_manager.reset_task_selection()

            except KeyboardInterrupt:
                self.ui.display_warning("Operation cancelled by user")
                break
            except Exception as e:
                self.logger.exception(f"Error in main loop: {e}")
                self.ui.display_error(f"An error occurred: {e}")
                # Reset state on error
                self.app_manager.reset_model_selection()
                self.app_manager.reset_task_selection()

    def _handle_model_selection(self) -> str:
        """
        Handle model selection.
        
        Returns:
            Selected model key, "exit", or None for invalid choice
        """
        available_models = self.app_manager.get_available_models()

        if not available_models:
            self.ui.display_error("No models available. Please check your configuration.")
            self.app_manager.exit_application()
            return "exit"

        return self.ui.select_model(available_models)

    def _handle_text_processing(self):
        """Handle text input and processing."""
        task_name = self.app_manager.app_state.selected_task['name']

        # Get text input
        can_use_previous = self.app_manager.can_use_previous_result()
        previous_result = self.app_manager.get_previous_result() if can_use_previous else None

        text_input = self.ui.get_text_input(task_name, can_use_previous, previous_result)

        if text_input is None:
            # User cancelled input
            return

        if not text_input.strip():
            self.ui.display_warning("No text provided. Please enter some text to process.")
            return

        # Process the text
        self.ui.display_status("Processing text...", "loading")
        result = self.app_manager.process_text(text_input)

        # Display result
        self.ui.display_result(result)

    def _handle_post_processing(self) -> bool:
        """
        Handle post-processing options (refine further, save, etc.).
        
        Returns:
            True to continue with current selections, False to reset to main menu
        """
        # Check if user can refine further
        if self.app_manager.should_refine_further():
            if self.ui.get_refine_choice():
                # User wants to refine further, keep current selections
                return True
            else:
                # User wants to go back to main menu
                return False

        # For non-refinement tasks, ask about saving (optional feature)
        if self.ui.get_save_choice():
            self._save_result()

        # Always return to main menu for non-refinement tasks
        return False

    def _save_result(self):
        """Save the result to a file (placeholder implementation)."""
        # This is a placeholder for future file saving functionality
        self.ui.display_status("File saving not yet implemented", "warning")
        # TODO: Implement file saving functionality
        # - Ask user for filename
        # - Save result to file
        # - Display success/error message


def main():
    """Main entry point for the application."""
    app = AIRefinerApp()
    app.run()


if __name__ == "__main__":
    main()
