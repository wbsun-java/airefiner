"""
AIRefiner Web Server
====================
Flask-based web interface for AIRefiner.
Reuses the EXACT same core business logic as the CLI (core.app_manager).
Zero modifications to existing code.

Run via:  python web_main.py   (from the project root)
CLI mode: python main.py
"""

import sys
import os

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so imports work (same as CLI main.py)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from utils.error_handler import ProcessingError

# Load .env exactly as CLI main.py does
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

from config.config_manager import load_config, get_config, TASKS
from core.app_manager import ApplicationManager

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config['JSON_AS_ASCII'] = False  # Support Chinese characters in JSON

    # ------------------------------------------------------------------
    # Initialise the shared ApplicationManager once at startup
    # ------------------------------------------------------------------
    try:
        load_config()
        manager = ApplicationManager()
        manager.initialize()
    except Exception as exc:
        # Store the error; API endpoints will surface it gracefully
        manager = None
        _init_error = str(exc)
    else:
        _init_error = None

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/status')
    def api_status():
        """Health check — returns available models and tasks."""
        if manager is None:
            return jsonify({'ok': False, 'error': _init_error}), 503

        models = manager.get_available_models()
        tasks = [
            {'key': k, 'id': v['id'], 'name': v['name']}
            for k, v in TASKS.items()
        ]
        return jsonify({'ok': True, 'models': models, 'tasks': tasks})

    @app.route('/api/refresh', methods=['POST'])
    def api_refresh():
        """Force a re-fetch of models from all providers, bypassing the 1-hour cache."""
        if manager is None:
            return jsonify({'ok': False, 'error': _init_error}), 503
        try:
            import models.model_loader as ml
            # Reset the module-level cache so next call re-fetches from APIs
            ml._model_cache = {}
            ml._cache_timestamp = 0
            new_models, errors = ml.initialize_models()
            manager._models = new_models
            manager._initialization_errors = errors
            models_list = manager.get_available_models()
            return jsonify({'ok': True, 'models': models_list, 'count': len(models_list)})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

    @app.route('/api/refine', methods=['POST'])
    def api_refine():
        """
        Process text through the selected model and task.

        Body (JSON):
            model   : str  — model key, e.g. "anthropic/Claude Sonnet 4"
            task_key: str  — task key "1", "2", or "3"
            text    : str  — text to process
        """
        if manager is None:
            return jsonify({'ok': False, 'error': _init_error}), 503

        data = request.get_json(force=True, silent=True) or {}
        model = (data.get('model') or '').strip()
        task_key = (data.get('task_key') or '').strip()
        text = (data.get('text') or '').strip()

        # Validate
        if not model:
            return jsonify({'ok': False, 'error': 'model is required'}), 400
        if task_key not in TASKS:
            return jsonify({'ok': False, 'error': f'task_key must be one of {list(TASKS.keys())}'}), 400
        if not text:
            return jsonify({'ok': False, 'error': 'text is required'}), 400

        available = manager.get_available_models()
        if model not in available:
            return jsonify({'ok': False, 'error': f'Unknown model: {model}'}), 400

        # --- Stateless execution: derive task_id from request, call processor directly ---
        # Do NOT mutate manager.selected_task / manager.selected_model — those are CLI state.
        task = TASKS[task_key]
        task_id = task['id']

        try:
            result = manager.task_processor.execute_task(model, text, task_id)
            return jsonify({'ok': True, 'result': result, 'model': model, 'task': task['name']})
        except ProcessingError as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
        except Exception as e:
            return jsonify({'ok': False, 'error': f'Unexpected error: {e}'}), 500

    return app
