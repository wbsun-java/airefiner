"""
Application manager for AIRefiner - separates business logic from UI logic.
"""

from typing import Dict, Any, Optional, Tuple

from config.constants import TaskConfiguration
from models import model_loader
from utils.error_handler import ErrorHandler, ModelInitializationError, ProcessingError, with_error_handling
from utils.logger import LoggerMixin


class AppState:
    """Application state management."""

    def __init__(self):
        self.selected_model: Optional[str] = None
        self.selected_task: Optional[Dict[str, Any]] = None
        self.last_result: Optional[str] = None
        self.should_exit: bool = False
        self.initialized_models: Dict[str, Any] = {}
        self.initialization_errors: Dict[str, str] = {}


class ModelManager(LoggerMixin):
    """Manages AI model initialization and access."""

    def __init__(self):
        super().__init__()
        self._models: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}
        self._initialized = False

    @with_error_handling("Model initialization", return_on_error=({}, {}))
    def initialize_models(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Initialize all AI models.
        
        Returns:
            Tuple of (initialized_models, initialization_errors)
            
        Raises:
            ModelInitializationError: If no models are successfully initialized
        """
        self.logger.info("Attempting to initialize AI models...")

        try:
            self._models, self._errors = model_loader.initialize_models()

            if not self._models:
                error_msg = "No AI models were successfully initialized."

                if self._errors:
                    error_details = "\n".join(f"- {key}: {error_msg}" for key, error_msg in self._errors.items())
                    error_msg += f"\nErrors:\n{error_details}"
                else:
                    error_msg += "\nPlease check your .env file for correct API keys and network connection."

                raise ModelInitializationError(error_msg, "all_models")

            self._initialized = True
            self.logger.info(f"Successfully initialized {len(self._models)} models")
            return self._models, self._errors

        except ModelInitializationError:
            raise  # Re-raise our custom error
        except Exception as e:
            raise ModelInitializationError(
                f"Unexpected error during model initialization: {e}",
                "model_loader",
                e
            )

    def get_models(self) -> Dict[str, Any]:
        """Get initialized models."""
        if not self._initialized:
            raise RuntimeError("Models not initialized. Call initialize_models() first.")
        return self._models

    def get_model(self, model_key: str) -> Optional[Any]:
        """Get a specific model by key."""
        return self._models.get(model_key)

    def get_available_model_keys(self) -> list[str]:
        """Get sorted list of available model keys."""
        return sorted(self._models.keys())


class TaskProcessor(LoggerMixin):
    """Handles task processing and model execution."""

    def __init__(self, model_manager: ModelManager):
        super().__init__()
        self.model_manager = model_manager

    def execute_task(self, model_key: str, text_input: str, task_id: str) -> str:
        """
        Execute a task using the specified model.
        
        Args:
            model_key: Key of the model to use
            text_input: Input text to process
            task_id: ID of the task to execute
            
        Returns:
            Result of the task execution
        """
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            from utils.translation_handler import TranslationHandler
            from prompts import refine_prompts

            model_instance = self.model_manager.get_model(model_key)
            if not model_instance:
                raise ProcessingError(f"Model '{model_key}' not found", task_id)

            output_parser = StrOutputParser()

            # Get appropriate prompt based on task
            if task_id == TaskConfiguration.AUTO_TRANSLATE:
                handler = TranslationHandler()
                prompt_template_str = handler.get_translation_prompt(text_input)
            else:
                prompt_map = {
                    TaskConfiguration.REFINE: refine_prompts.REFINE_TEXT_PROMPT,
                    "refine_presentation": refine_prompts.REFINE_PRESENTATION_PROMPT,
                }
                prompt_template_str = prompt_map.get(task_id)

            if not prompt_template_str:
                raise ProcessingError(f"Prompt for task '{task_id}' not found", task_id)

            # Execute the chain
            prompt_template = ChatPromptTemplate.from_template(prompt_template_str)
            chain = prompt_template | model_instance | output_parser

            self.logger.info(f"Executing task '{task_id}' with model '{model_key}'")
            result = chain.invoke({"user_text": text_input})
            self.logger.info(f"Task execution completed successfully")

            return result

        except ProcessingError:
            raise  # Re-raise our custom error
        except Exception as e:
            error_handler = ErrorHandler()
            error_msg = error_handler.handle_error(e, f"Task execution ({task_id})")
            raise ProcessingError(error_msg, task_id, e)


class ApplicationManager(LoggerMixin):
    """Main application manager that coordinates all components."""

    def __init__(self):
        super().__init__()
        self.app_state = AppState()
        self.model_manager = ModelManager()
        self.task_processor = TaskProcessor(self.model_manager)

    def initialize(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Initialize the application.
        
        Returns:
            Tuple of (initialized_models, initialization_errors)
        """
        models, errors = self.model_manager.initialize_models()
        self.app_state.initialized_models = models
        self.app_state.initialization_errors = errors
        return models, errors

    def get_available_models(self) -> list[str]:
        """Get list of available model keys."""
        return self.model_manager.get_available_model_keys()

    def set_selected_model(self, model_key: str):
        """Set the selected model."""
        self.app_state.selected_model = model_key
        self.logger.info(f"Selected model: {model_key}")

    def set_selected_task(self, task: Dict[str, Any]):
        """Set the selected task."""
        self.app_state.selected_task = task
        self.logger.info(f"Selected task: {task.get('name', 'Unknown')}")

    def process_text(self, text_input: str) -> str:
        """
        Process text using the current model and task.
        
        Args:
            text_input: Input text to process
            
        Returns:
            Processed text result
        """
        try:
            if not self.app_state.selected_model:
                raise ProcessingError("No model selected", "unknown")

            if not self.app_state.selected_task:
                raise ProcessingError("No task selected", "unknown")

            result = self.task_processor.execute_task(
                self.app_state.selected_model,
                text_input,
                self.app_state.selected_task['id']
            )

            self.app_state.last_result = result
            return result

        except ProcessingError as e:
            error_handler = ErrorHandler()
            error_msg = error_handler.handle_error(e, "Text processing")
            self.app_state.last_result = None
            return f"Error: {error_msg}"
        except Exception as e:
            error_handler = ErrorHandler()
            error_msg = error_handler.handle_error(e, "Text processing")
            self.app_state.last_result = None
            return f"Unexpected error: {error_msg}"

    def should_refine_further(self) -> bool:
        """Check if the user can refine the result further."""
        return (self.app_state.selected_task and
                self.app_state.selected_task['id'] == TaskConfiguration.REFINE and
                self.app_state.last_result and
                "Error" not in self.app_state.last_result)

    def can_use_previous_result(self) -> bool:
        """Check if the previous result can be used as input."""
        return (self.app_state.selected_task and
                self.app_state.selected_task['id'] == TaskConfiguration.REFINE and
                self.app_state.last_result is not None)

    def get_previous_result(self) -> Optional[str]:
        """Get the previous result."""
        return self.app_state.last_result

    def reset_model_selection(self):
        """Reset model selection."""
        self.app_state.selected_model = None

    def reset_task_selection(self):
        """Reset task selection."""
        self.app_state.selected_task = None

    def exit_application(self):
        """Signal application exit."""
        self.app_state.should_exit = True
        self.logger.info("Application exit requested")

    def should_exit(self) -> bool:
        """Check if application should exit."""
        return self.app_state.should_exit
