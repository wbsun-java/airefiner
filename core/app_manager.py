"""
Application manager for AIRefiner - separates business logic from UI logic.
"""

from typing import Dict, Any, Optional, Tuple
from config.constants import TaskConfiguration
from models import model_loader
from utils.error_handler import handle_error, ModelInitializationError, ProcessingError, CircuitBreaker
from utils.logger import LoggerMixin


class TaskProcessor(LoggerMixin):
    """Handles task processing and model execution."""

    def __init__(self, get_model):
        super().__init__()
        self.get_model = get_model
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._translation_handler = None

    def execute_task(self, model_key: str, text_input: str, task_id: str) -> str:
        try:
            if model_key not in self.circuit_breakers:
                self.logger.info(f"Creating new circuit breaker for model '{model_key}'")
                self.circuit_breakers[model_key] = CircuitBreaker(name=model_key)
            circuit_breaker = self.circuit_breakers[model_key]

            from prompts import refine_prompts

            model_callable = self.get_model(model_key)
            if not model_callable:
                raise ProcessingError(f"Model '{model_key}' not found", task_id)

            if task_id == TaskConfiguration.AUTO_TRANSLATE:
                if self._translation_handler is None:
                    from utils.translation_handler import TranslationHandler
                    self._translation_handler = TranslationHandler()
                prompt_template_str = self._translation_handler.get_translation_prompt(text_input)
            else:
                prompt_map = {
                    TaskConfiguration.REFINE: refine_prompts.REFINE_TEXT_PROMPT,
                    TaskConfiguration.REFINE_PRESENTATION: refine_prompts.REFINE_PRESENTATION_PROMPT,
                }
                prompt_template_str = prompt_map.get(task_id)

            if not prompt_template_str:
                raise ProcessingError(f"Prompt for task '{task_id}' not found", task_id)

            formatted_prompt = prompt_template_str.format(user_text=text_input)

            self.logger.info(f"Executing task '{task_id}' with model '{model_key}'")
            result = circuit_breaker.call(model_callable, formatted_prompt)
            self.logger.info("Task execution completed successfully")
            return result

        except ProcessingError:
            raise
        except Exception as e:
            error_msg = handle_error(e, f"Task execution ({task_id})")
            raise ProcessingError(error_msg, task_id, e)


class ApplicationManager(LoggerMixin):
    """Main application manager that coordinates all components."""

    def __init__(self):
        super().__init__()
        self.selected_model: Optional[str] = None
        self.selected_task: Optional[Dict[str, Any]] = None
        self.last_result: Optional[str] = None
        self.last_result_task_id: Optional[str] = None
        self.last_result_is_error: bool = False
        self._exit_requested: bool = False
        self._models: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}

        self.task_processor = TaskProcessor(self._get_model)

    def _get_model(self, model_key: str) -> Optional[Any]:
        return self._models.get(model_key)

    def initialize(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        self.logger.info("Attempting to initialize AI models...")
        try:
            self._models, self._errors = model_loader.initialize_models()

            if not self._models:
                msg = "No AI models were successfully initialized."
                if self._errors:
                    details = "\n".join(f"- {key}: {err}" for key, err in self._errors.items())
                    msg += f"\nErrors:\n{details}"
                else:
                    msg += "\nPlease check your .env file for correct API keys and network connection."
                raise ModelInitializationError(msg, "all_models")

            self.logger.info(f"Successfully initialized {len(self._models)} models")
            return self._models, self._errors

        except ModelInitializationError:
            raise
        except Exception as e:
            raise ModelInitializationError(
                f"Unexpected error during model initialization: {e}",
                "model_loader", e
            )

    def get_available_models(self) -> list[str]:
        return sorted(self._models.keys())

    def process_text(self, text_input: str) -> str:
        try:
            if not self.selected_model:
                raise ProcessingError("No model selected", "unknown")
            if not self.selected_task:
                raise ProcessingError("No task selected", "unknown")

            result = self.task_processor.execute_task(
                self.selected_model, text_input, self.selected_task['id']
            )
            self.last_result = result
            self.last_result_task_id = self.selected_task['id']
            self.last_result_is_error = False
            return result

        except ProcessingError as e:
            error_msg = handle_error(e, "Text processing")
            self.last_result = None
            self.last_result_task_id = None
            self.last_result_is_error = True
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = handle_error(e, "Text processing")
            self.last_result = None
            self.last_result_task_id = None
            self.last_result_is_error = True
            return f"Unexpected error: {error_msg}"

    def should_refine_further(self) -> bool:
        return (self.selected_task is not None and
                self.last_result is not None and
                not self.last_result_is_error)

    def can_use_previous_result(self) -> bool:
        return (self.selected_task is not None and
                self.last_result is not None and
                self.last_result_task_id == self.selected_task['id'])

    def get_previous_result(self) -> Optional[str]:
        return self.last_result

    def reset_state(self):
        self.selected_model = None
        self.selected_task = None
        self.last_result = None
        self.last_result_task_id = None
        self.last_result_is_error = False

    def exit_application(self):
        self._exit_requested = True
        self.logger.info("Application exit requested")

    def is_exit_requested(self) -> bool:
        return self._exit_requested
