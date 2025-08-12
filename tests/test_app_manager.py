"""
Unit tests for application manager components.
"""

from unittest.mock import Mock, patch

import pytest

from core.app_manager import AppState, ModelManager, TaskProcessor, ApplicationManager
from utils.error_handler import ModelInitializationError, ProcessingError


class TestAppState:
    """Test AppState class."""

    def test_app_state_initialization(self):
        """Test AppState initializes with correct defaults."""
        state = AppState()

        assert state.selected_model is None
        assert state.selected_task is None
        assert state.last_result is None
        assert state.should_exit is False
        assert state.initialized_models == {}
        assert state.initialization_errors == {}


class TestModelManager:
    """Test ModelManager class."""

    @pytest.fixture
    def model_manager(self):
        """Create ModelManager for testing."""
        return ModelManager()

    @patch('core.app_manager.model_loader.initialize_models')
    def test_initialize_models_success(self, mock_initialize, model_manager):
        """Test successful model initialization."""
        mock_models = {'model1': Mock(), 'model2': Mock()}
        mock_errors = {'model3': 'Failed to initialize'}
        mock_initialize.return_value = (mock_models, mock_errors)

        models, errors = model_manager.initialize_models()

        assert models == mock_models
        assert errors == mock_errors
        assert model_manager._initialized is True
        mock_initialize.assert_called_once()

    @patch('core.app_manager.model_loader.initialize_models')
    def test_initialize_models_no_models(self, mock_initialize, model_manager):
        """Test initialization when no models are available."""
        mock_initialize.return_value = ({}, {'error': 'No API keys'})

        with pytest.raises(ModelInitializationError) as exc_info:
            model_manager.initialize_models()

        assert "No AI models were successfully initialized" in str(exc_info.value)
        assert model_manager._initialized is False

    @patch('core.app_manager.model_loader.initialize_models')
    def test_initialize_models_exception(self, mock_initialize, model_manager):
        """Test initialization when loader raises exception."""
        mock_initialize.side_effect = RuntimeError("Loader failed")

        with pytest.raises(ModelInitializationError) as exc_info:
            model_manager.initialize_models()

        assert "Unexpected error during model initialization" in str(exc_info.value)
        assert exc_info.value.original_error.__class__ == RuntimeError

    def test_get_models_not_initialized(self, model_manager):
        """Test getting models when not initialized."""
        with pytest.raises(RuntimeError, match="Models not initialized"):
            model_manager.get_models()

    def test_get_models_initialized(self, model_manager):
        """Test getting models when initialized."""
        test_models = {'model1': Mock()}
        model_manager._models = test_models
        model_manager._initialized = True

        models = model_manager.get_models()
        assert models == test_models

    def test_get_model_existing(self, model_manager):
        """Test getting existing model."""
        test_model = Mock()
        model_manager._models = {'test_model': test_model}

        model = model_manager.get_model('test_model')
        assert model is test_model

    def test_get_model_nonexistent(self, model_manager):
        """Test getting non-existent model."""
        model_manager._models = {}

        model = model_manager.get_model('nonexistent')
        assert model is None

    def test_get_available_model_keys(self, model_manager):
        """Test getting available model keys."""
        model_manager._models = {'model2': Mock(), 'model1': Mock(), 'model3': Mock()}

        keys = model_manager.get_available_model_keys()
        assert keys == ['model1', 'model2', 'model3']  # Should be sorted


class TestTaskProcessor:
    """Test TaskProcessor class."""

    @pytest.fixture
    def mock_model_manager(self):
        """Create mock ModelManager."""
        manager = Mock(spec=ModelManager)
        return manager

    @pytest.fixture
    def task_processor(self, mock_model_manager):
        """Create TaskProcessor for testing."""
        return TaskProcessor(mock_model_manager)

    def test_execute_task_model_not_found(self, task_processor, mock_model_manager):
        """Test task execution when model is not found."""
        mock_model_manager.get_model.return_value = None

        with pytest.raises(ProcessingError) as exc_info:
            task_processor.execute_task('nonexistent_model', 'test input', 'refine')

        assert "Model 'nonexistent_model' not found" in str(exc_info.value)
        assert exc_info.value.task_id == 'refine'

    @patch('core.app_manager.refine_prompts')
    @patch('core.app_manager.ChatPromptTemplate')
    @patch('core.app_manager.StrOutputParser')
    def test_execute_task_success(self, mock_parser, mock_template, mock_prompts,
                                  task_processor, mock_model_manager):
        """Test successful task execution."""
        # Setup mocks
        mock_model = Mock()
        mock_model_manager.get_model.return_value = mock_model
        mock_prompts.REFINE_TEXT_PROMPT = "Test prompt: {user_text}"

        mock_prompt_template = Mock()
        mock_template.from_template.return_value = mock_prompt_template

        mock_chain = Mock()
        mock_prompt_template.__or__ = Mock(return_value=mock_chain)
        mock_chain.invoke.return_value = "Processed text"

        # Execute
        result = task_processor.execute_task('test_model', 'input text', 'refine')

        # Verify
        assert result == "Processed text"
        mock_model_manager.get_model.assert_called_once_with('test_model')
        mock_template.from_template.assert_called_once_with("Test prompt: {user_text}")
        mock_chain.invoke.assert_called_once_with({"user_text": "input text"})

    @patch('core.app_manager.TranslationHandler')
    def test_execute_task_auto_translate(self, mock_handler_class, task_processor, mock_model_manager):
        """Test task execution with auto-translate."""
        # Setup mocks
        mock_model = Mock()
        mock_model_manager.get_model.return_value = mock_model

        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_handler.get_translation_prompt.return_value = "Translation prompt: {user_text}"

        with patch('core.app_manager.ChatPromptTemplate') as mock_template, \
                patch('core.app_manager.StrOutputParser'):
            mock_prompt_template = Mock()
            mock_template.from_template.return_value = mock_prompt_template

            mock_chain = Mock()
            mock_prompt_template.__or__ = Mock(return_value=mock_chain)
            mock_chain.invoke.return_value = "Translated text"

            result = task_processor.execute_task('test_model', 'input text', 'auto_translate')

            assert result == "Translated text"
            mock_handler.get_translation_prompt.assert_called_once_with('input text')

    def test_execute_task_unknown_task_id(self, task_processor, mock_model_manager):
        """Test task execution with unknown task ID."""
        mock_model = Mock()
        mock_model_manager.get_model.return_value = mock_model

        with pytest.raises(ProcessingError) as exc_info:
            task_processor.execute_task('test_model', 'input text', 'unknown_task')

        assert "Prompt for task 'unknown_task' not found" in str(exc_info.value)
        assert exc_info.value.task_id == 'unknown_task'

    @patch('core.app_manager.ChatPromptTemplate')
    @patch('core.app_manager.refine_prompts')
    def test_execute_task_chain_exception(self, mock_prompts, mock_template,
                                          task_processor, mock_model_manager):
        """Test task execution when chain raises exception."""
        # Setup mocks
        mock_model = Mock()
        mock_model_manager.get_model.return_value = mock_model
        mock_prompts.REFINE_TEXT_PROMPT = "Test prompt: {user_text}"

        mock_prompt_template = Mock()
        mock_template.from_template.return_value = mock_prompt_template

        mock_chain = Mock()
        mock_prompt_template.__or__ = Mock(return_value=mock_chain)
        mock_chain.invoke.side_effect = RuntimeError("Chain failed")

        with patch('core.app_manager.StrOutputParser'), \
                patch('core.app_manager.ErrorHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            mock_handler.handle_error.return_value = "Error handled"

            with pytest.raises(ProcessingError) as exc_info:
                task_processor.execute_task('test_model', 'input text', 'refine')

            assert exc_info.value.task_id == 'refine'
            assert exc_info.value.original_error.__class__ == RuntimeError


class TestApplicationManager:
    """Test ApplicationManager class."""

    @pytest.fixture
    def app_manager(self):
        """Create ApplicationManager for testing."""
        return ApplicationManager()

    @patch.object(ModelManager, 'initialize_models')
    def test_initialize(self, mock_initialize, app_manager):
        """Test application initialization."""
        mock_models = {'model1': Mock()}
        mock_errors = {'model2': 'Error'}
        mock_initialize.return_value = (mock_models, mock_errors)

        models, errors = app_manager.initialize()

        assert models == mock_models
        assert errors == mock_errors
        assert app_manager.app_state.initialized_models == mock_models
        assert app_manager.app_state.initialization_errors == mock_errors

    def test_get_available_models(self, app_manager):
        """Test getting available models."""
        with patch.object(app_manager.model_manager, 'get_available_model_keys') as mock_get_keys:
            mock_get_keys.return_value = ['model1', 'model2']

            models = app_manager.get_available_models()

            assert models == ['model1', 'model2']
            mock_get_keys.assert_called_once()

    def test_set_selected_model(self, app_manager):
        """Test setting selected model."""
        app_manager.set_selected_model('test_model')

        assert app_manager.app_state.selected_model == 'test_model'

    def test_set_selected_task(self, app_manager):
        """Test setting selected task."""
        test_task = {'id': 'refine', 'name': 'Refine Text'}
        app_manager.set_selected_task(test_task)

        assert app_manager.app_state.selected_task == test_task

    def test_process_text_no_model(self, app_manager):
        """Test processing text with no model selected."""
        result = app_manager.process_text("test input")

        assert "No model selected" in result
        assert app_manager.app_state.last_result is None

    def test_process_text_no_task(self, app_manager):
        """Test processing text with no task selected."""
        app_manager.app_state.selected_model = 'test_model'

        result = app_manager.process_text("test input")

        assert "No task selected" in result
        assert app_manager.app_state.last_result is None

    def test_process_text_success(self, app_manager):
        """Test successful text processing."""
        app_manager.app_state.selected_model = 'test_model'
        app_manager.app_state.selected_task = {'id': 'refine', 'name': 'Refine'}

        with patch.object(app_manager.task_processor, 'execute_task') as mock_execute:
            mock_execute.return_value = "Processed text"

            result = app_manager.process_text("test input")

            assert result == "Processed text"
            assert app_manager.app_state.last_result == "Processed text"
            mock_execute.assert_called_once_with('test_model', 'test input', 'refine')

    def test_process_text_processing_error(self, app_manager):
        """Test text processing with ProcessingError."""
        app_manager.app_state.selected_model = 'test_model'
        app_manager.app_state.selected_task = {'id': 'refine', 'name': 'Refine'}

        with patch.object(app_manager.task_processor, 'execute_task') as mock_execute, \
                patch('core.app_manager.ErrorHandler') as mock_handler_class:
            mock_execute.side_effect = ProcessingError("Processing failed", "refine")
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            mock_handler.handle_error.return_value = "Error message"

            result = app_manager.process_text("test input")

            assert "Error: Error message" in result
            assert app_manager.app_state.last_result is None

    def test_should_refine_further_true_refine_task(self, app_manager):
        """Test should_refine_further returns True for refine task when conditions met."""
        app_manager.app_state.selected_task = {'id': 'refine'}
        app_manager.app_state.last_result = "Some result"

        assert app_manager.should_refine_further() is True

    def test_should_refine_further_true_translate_task(self, app_manager):
        """Test should_refine_further returns True for translate task (now supported)."""
        app_manager.app_state.selected_task = {'id': 'translate'}
        app_manager.app_state.last_result = "Some result"

        assert app_manager.should_refine_further() is True

    def test_should_refine_further_true_presentation_task(self, app_manager):
        """Test should_refine_further returns True for presentation task (now supported)."""
        app_manager.app_state.selected_task = {'id': 'refine_presentation'}
        app_manager.app_state.last_result = "Some result"

        assert app_manager.should_refine_further() is True

    def test_should_refine_further_false_error_result(self, app_manager):
        """Test should_refine_further returns False when result contains error."""
        app_manager.app_state.selected_task = {'id': 'refine'}
        app_manager.app_state.last_result = "Error: Something went wrong"

        assert app_manager.should_refine_further() is False

    def test_can_use_previous_result_true_refine_task(self, app_manager):
        """Test can_use_previous_result returns True for refine task when conditions met."""
        app_manager.app_state.selected_task = {'id': 'refine'}
        app_manager.app_state.last_result = "Previous result"

        assert app_manager.can_use_previous_result() is True

    def test_can_use_previous_result_true_translate_task(self, app_manager):
        """Test can_use_previous_result returns True for translate task (now supported)."""
        app_manager.app_state.selected_task = {'id': 'auto_translate'}
        app_manager.app_state.last_result = "Previous result"

        assert app_manager.can_use_previous_result() is True

    def test_can_use_previous_result_true_presentation_task(self, app_manager):
        """Test can_use_previous_result returns True for presentation task (now supported)."""
        app_manager.app_state.selected_task = {'id': 'refine_presentation'}
        app_manager.app_state.last_result = "Previous result"

        assert app_manager.can_use_previous_result() is True

    def test_can_use_previous_result_false_no_result(self, app_manager):
        """Test can_use_previous_result returns False with no previous result."""
        app_manager.app_state.selected_task = {'id': 'refine'}
        app_manager.app_state.last_result = None

        assert app_manager.can_use_previous_result() is False

    def test_get_previous_result(self, app_manager):
        """Test getting previous result."""
        app_manager.app_state.last_result = "Previous result"

        result = app_manager.get_previous_result()
        assert result == "Previous result"

    def test_reset_model_selection(self, app_manager):
        """Test resetting model selection."""
        app_manager.app_state.selected_model = 'test_model'

        app_manager.reset_model_selection()

        assert app_manager.app_state.selected_model is None

    def test_reset_task_selection(self, app_manager):
        """Test resetting task selection."""
        app_manager.app_state.selected_task = {'id': 'refine'}

        app_manager.reset_task_selection()

        assert app_manager.app_state.selected_task is None

    def test_exit_application(self, app_manager):
        """Test exiting application."""
        app_manager.exit_application()

        assert app_manager.app_state.should_exit is True

    def test_should_exit(self, app_manager):
        """Test checking if should exit."""
        assert app_manager.should_exit() is False

        app_manager.app_state.should_exit = True
        assert app_manager.should_exit() is True
