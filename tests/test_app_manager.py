"""
Unit tests for application manager components.
"""

from unittest.mock import Mock, patch

import pytest

from core.app_manager import TaskProcessor, ApplicationManager
from utils.error_handler import ModelInitializationError, ProcessingError


class TestTaskProcessor:
    """Test TaskProcessor class."""

    @pytest.fixture
    def mock_get_model(self):
        return Mock()

    @pytest.fixture
    def task_processor(self, mock_get_model):
        return TaskProcessor(mock_get_model)

    def test_execute_task_model_not_found(self, task_processor, mock_get_model):
        mock_get_model.return_value = None

        with pytest.raises(ProcessingError) as exc_info:
            task_processor.execute_task('nonexistent_model', 'test input', 'refine')

        assert "Model 'nonexistent_model' not found" in str(exc_info.value)
        assert exc_info.value.task_id == 'refine'

    def test_execute_task_unknown_task_id(self, task_processor, mock_get_model):
        mock_get_model.return_value = Mock()

        with pytest.raises(ProcessingError) as exc_info:
            task_processor.execute_task('test_model', 'input text', 'unknown_task')

        assert "Prompt for task 'unknown_task' not found" in str(exc_info.value)
        assert exc_info.value.task_id == 'unknown_task'

    def test_execute_task_success(self, task_processor, mock_get_model):
        mock_model = Mock(return_value="Processed text")
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Test prompt: {user_text}"
            result = task_processor.execute_task('test_model', 'input text', 'refine')

        assert result == "Processed text"
        mock_model.assert_called_once_with("Test prompt: input text")

    def test_execute_task_chain_exception(self, task_processor, mock_get_model):
        mock_model = Mock(side_effect=RuntimeError("API call failed"))
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Test prompt: {user_text}"
            with pytest.raises(ProcessingError) as exc_info:
                task_processor.execute_task('test_model', 'input text', 'refine')

        assert exc_info.value.task_id == 'refine'
        assert isinstance(exc_info.value.original_error, RuntimeError)

    def test_circuit_breaker_opens_after_threshold_failures(
        self, task_processor, mock_get_model
    ):
        # Default threshold is 3 failures
        mock_model = Mock(side_effect=RuntimeError("API down"))
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            for _ in range(3):
                with pytest.raises(ProcessingError):
                    task_processor.execute_task('test_model', 'input', 'refine')

        cb = task_processor.circuit_breakers['test_model']
        from utils.error_handler import CircuitBreaker
        assert cb.state == CircuitBreaker.STATE_OPEN

    def test_open_circuit_raises_without_calling_model(
        self, task_processor, mock_get_model
    ):
        from utils.error_handler import CircuitBreaker, APIError
        mock_model = Mock(side_effect=RuntimeError("API down"))
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            for _ in range(3):
                with pytest.raises(ProcessingError):
                    task_processor.execute_task('test_model', 'input', 'refine')

        # 4th call — circuit is open, model should NOT be called
        mock_model.reset_mock()
        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            with pytest.raises(ProcessingError) as exc_info:
                task_processor.execute_task('test_model', 'input', 'refine')

        mock_model.assert_not_called()
        assert isinstance(exc_info.value.original_error, APIError)

    def test_each_model_key_has_independent_circuit_breaker(
        self, task_processor, mock_get_model
    ):
        failing_model = Mock(side_effect=RuntimeError("down"))
        passing_model = Mock(return_value="ok")

        def get_model(key):
            return failing_model if key == 'bad_model' else passing_model

        mock_get_model.side_effect = get_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Prompt: {user_text}"
            for _ in range(3):
                with pytest.raises(ProcessingError):
                    task_processor.execute_task('bad_model', 'input', 'refine')

            # good_model has its own circuit breaker — should still work
            result = task_processor.execute_task('good_model', 'input', 'refine')

        assert result == "ok"
        assert 'bad_model' in task_processor.circuit_breakers
        assert 'good_model' in task_processor.circuit_breakers

    def test_prompt_format_passes_through_curly_braces_in_input(
        self, task_processor, mock_get_model
    ):
        # User input may contain JSON or template-like strings with braces.
        # str.format() should substitute {user_text} in the template and leave
        # braces inside the substituted value untouched.
        mock_model = Mock(return_value="done")
        mock_get_model.return_value = mock_model

        with patch('prompts.refine_prompts') as mock_prompts:
            mock_prompts.REFINE_TEXT_PROMPT = "Refine: {user_text}"
            result = task_processor.execute_task(
                'test_model', '{"key": "value"}', 'refine'
            )

        assert result == "done"
        mock_model.assert_called_once_with('Refine: {"key": "value"}')

    @patch('utils.translation_handler.TranslationHandler')
    def test_execute_task_auto_translate(self, mock_handler_cls, task_processor, mock_get_model):
        mock_model = Mock(return_value="Translated text")
        mock_get_model.return_value = mock_model

        mock_handler = Mock()
        mock_handler_cls.return_value = mock_handler
        mock_handler.get_translation_prompt.return_value = "Translation prompt: {user_text}"

        result = task_processor.execute_task('test_model', 'input text', 'auto_translate')

        assert result == "Translated text"
        mock_handler.get_translation_prompt.assert_called_once_with('input text')
        mock_model.assert_called_once_with("Translation prompt: input text")


class TestApplicationManager:
    """Test ApplicationManager class."""

    @pytest.fixture
    def app_manager(self):
        return ApplicationManager()

    @patch('core.app_manager.model_loader.initialize_models')
    def test_initialize_success(self, mock_initialize, app_manager):
        mock_models = {'model1': Mock(), 'model2': Mock()}
        mock_errors = {'model3': 'Failed'}
        mock_initialize.return_value = (mock_models, mock_errors)

        models, errors = app_manager.initialize()

        assert models == mock_models
        assert errors == mock_errors
        assert app_manager._models == mock_models

    @patch('core.app_manager.model_loader.initialize_models')
    def test_initialize_no_models(self, mock_initialize, app_manager):
        mock_initialize.return_value = ({}, {'error': 'No API keys'})

        with pytest.raises(ModelInitializationError) as exc_info:
            app_manager.initialize()

        assert "No AI models were successfully initialized" in str(exc_info.value)

    @patch('core.app_manager.model_loader.initialize_models')
    def test_initialize_exception(self, mock_initialize, app_manager):
        mock_initialize.side_effect = RuntimeError("Loader failed")

        with pytest.raises(ModelInitializationError) as exc_info:
            app_manager.initialize()

        assert "Unexpected error during model initialization" in str(exc_info.value)
        assert isinstance(exc_info.value.original_error, RuntimeError)

    def test_get_available_models(self, app_manager):
        app_manager._models = {'model2': Mock(), 'model1': Mock(), 'model3': Mock()}
        assert app_manager.get_available_models() == ['model1', 'model2', 'model3']

    def test_process_text_no_model(self, app_manager):
        result = app_manager.process_text("test input")
        assert "No model selected" in result
        assert app_manager.last_result is None

    def test_process_text_no_task(self, app_manager):
        app_manager.selected_model = 'test_model'
        result = app_manager.process_text("test input")
        assert "No task selected" in result
        assert app_manager.last_result is None

    def test_process_text_success(self, app_manager):
        app_manager.selected_model = 'test_model'
        app_manager.selected_task = {'id': 'refine', 'name': 'Refine'}

        with patch.object(app_manager.task_processor, 'execute_task', return_value="Processed text"):
            result = app_manager.process_text("test input")

        assert result == "Processed text"
        assert app_manager.last_result == "Processed text"
        assert app_manager.last_result_task_id == "refine"

    def test_process_text_processing_error(self, app_manager):
        app_manager.selected_model = 'test_model'
        app_manager.selected_task = {'id': 'refine', 'name': 'Refine'}

        with patch.object(app_manager.task_processor, 'execute_task',
                          side_effect=ProcessingError("Processing failed", "refine")):
            result = app_manager.process_text("test input")

        assert "Error:" in result
        assert app_manager.last_result is None
        assert app_manager.last_result_is_error is True

    def test_should_refine_further_true(self, app_manager):
        app_manager.selected_task = {'id': 'refine'}
        app_manager.last_result = "Some result"
        assert app_manager.should_refine_further() is True

    def test_should_refine_further_false_error_result(self, app_manager):
        app_manager.selected_task = {'id': 'refine'}
        app_manager.last_result = "Error: Something"
        app_manager.last_result_is_error = True
        assert app_manager.should_refine_further() is False

    def test_can_use_previous_result_true(self, app_manager):
        app_manager.selected_task = {'id': 'refine'}
        app_manager.last_result = "Previous result"
        app_manager.last_result_task_id = "refine"
        assert app_manager.can_use_previous_result() is True

    def test_can_use_previous_result_false_no_result(self, app_manager):
        app_manager.selected_task = {'id': 'refine'}
        app_manager.last_result = None
        assert app_manager.can_use_previous_result() is False

    def test_can_use_previous_result_false_different_task(self, app_manager):
        app_manager.selected_task = {'id': 'auto_translate'}
        app_manager.last_result = "Previous result"
        app_manager.last_result_task_id = "refine"
        assert app_manager.can_use_previous_result() is False

    def test_get_previous_result(self, app_manager):
        app_manager.last_result = "Previous result"
        assert app_manager.get_previous_result() == "Previous result"

    def test_reset_state(self, app_manager):
        app_manager.selected_model = 'test_model'
        app_manager.selected_task = {'id': 'refine'}
        app_manager.last_result = "Some result"
        app_manager.last_result_task_id = "refine"

        app_manager.reset_state()

        assert app_manager.selected_model is None
        assert app_manager.selected_task is None
        assert app_manager.last_result is None
        assert app_manager.last_result_task_id is None
        assert app_manager.last_result_is_error is False

    def test_exit_application(self, app_manager):
        assert app_manager.is_exit_requested() is False
        app_manager.exit_application()
        assert app_manager.is_exit_requested() is True
