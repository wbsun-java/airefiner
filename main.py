"""
Main application entry point for AIRefiner.
"""

from dotenv import load_dotenv

# Load environment variables from .env file before other imports
load_dotenv()

from core.app_manager import ApplicationManager
from ui.console_interface import ConsoleInterface
from utils.logger import LoggerMixin
from config.config_manager import load_config, get_config


class AIRefinerApp(LoggerMixin):
    """Main application class that coordinates UI and business logic."""

    def __init__(self):
        super().__init__()
        self.app_manager = ApplicationManager()
        self.ui = ConsoleInterface()

    def run(self):
        try:
            self.logger.info("Starting AIRefiner application")
            self.ui.display_welcome_message()
            load_config()
            self.app_manager.initialize()
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
        tasks = get_config().tasks
        while not self.app_manager.is_exit_requested():
            try:
                if not self.app_manager.selected_model:
                    choice = self._handle_model_selection()
                    if choice == "exit":
                        self.app_manager.exit_application()
                        break
                    elif choice is None:
                        continue
                    self.app_manager.selected_model = choice

                if not self.app_manager.selected_task:
                    task = self.ui.select_task(tasks)
                    if task is None:
                        self.app_manager.selected_model = None
                        continue
                    self.app_manager.selected_task = task

                self._handle_text_processing()

                if not self._handle_post_processing():
                    self.app_manager.reset_state()

            except KeyboardInterrupt:
                self.ui.display_warning("Operation cancelled by user")
                break
            except Exception as e:
                self.logger.exception(f"Error in main loop: {e}")
                self.ui.display_error(f"An error occurred: {e}")
                self.app_manager.reset_state()

    def _handle_model_selection(self):
        available_models = self.app_manager.get_available_models()
        if not available_models:
            self.ui.display_error("No models available. Please check your configuration.")
            return "exit"
        return self.ui.select_model(available_models)

    def _handle_text_processing(self):
        task_name = self.app_manager.selected_task['name']
        can_use_previous = self.app_manager.can_use_previous_result()
        previous_result = self.app_manager.get_previous_result() if can_use_previous else None

        text_input = self.ui.get_text_input(task_name, can_use_previous, previous_result)
        if not text_input:
            return
        if not text_input.strip():
            self.ui.display_warning("No text provided. Please enter some text to process.")
            return

        self.ui.display_status("Processing text...", "loading")
        result = self.app_manager.process_text(text_input)
        self.ui.display_result(result)

    def _handle_post_processing(self) -> bool:
        if self.app_manager.should_refine_further():
            return self.ui.get_refine_choice()
        return False


def main():
    app = AIRefinerApp()
    app.run()


if __name__ == "__main__":
    main()
