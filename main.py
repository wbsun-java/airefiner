import sys
import traceback

from dotenv import load_dotenv

# Load environment variables from .env file before other imports
load_dotenv()

# --- Core Imports ---
from models import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Local Imports ---
from config import settings
from prompts import refine_prompts
from utils import input_helpers
from utils.translation_handler import TranslationHandler


class AppState:
    """A simple class to hold the application's state."""

    def __init__(self):
        self.selected_model = None
        self.selected_task = None
        self.last_result = None
        self.should_exit = False

def initialize_all_ai_models():
    """
    Initializes AI models by calling the main initializer function from model_loader.py.
    Handles and prints errors if initialization fails.
    """
    print("Attempting to initialize AI models...")
    try:
        initialized_models, init_errors = model_loader.initialize_models()

        if not initialized_models:
            print("\n--- FATAL ERROR: No AI models were successfully initialized. ---")
            if init_errors:
                print("The following errors occurred during initialization:")
                for key, error_msg in init_errors.items():
                    print(f"- {key}: {error_msg}")
            else:
                print("No specific errors were reported, but initialization failed.")
                print("Please check your .env file for correct API keys and network connection.")
            sys.exit(1)

        return initialized_models, init_errors

    except Exception as e:
        print(f"\n--- FATAL UNHANDLED EXCEPTION during model initialization ---")
        print(f"An unexpected error occurred in 'model_loader.py': {e}")
        traceback.print_exc()
        sys.exit(1)


def display_menu(title, options, exit_option_label="Exit"):
    """A generic function to display a numbered menu and get user choice."""
    print(f"\n--- {title} ---")
    for key, value in options.items():
        print(f"{key}. {value}")
    if exit_option_label:
        print(f"0. {exit_option_label}")
    return input("Enter choice: ").strip()


def select_model(available_models):
    """Handles the model selection UI. Returns the selected model key or None."""
    model_options = {str(i + 1): name for i, name in enumerate(available_models)}
    choice = display_menu("Select a Model", model_options)
    if choice == "0":
        return "exit"  # Special value to signal exit
    try:
        return available_models[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Please try again.")
        return None


def select_task():
    """Handles the task selection UI. Returns the selected task object or None."""
    task_options = {key: info['name'] for key, info in settings.TASKS.items()}
    choice = display_menu("Select a Task", task_options, "Back to model selection")
    if choice == "0":
        return None
    return settings.TASKS.get(choice)


def get_user_input(app_state):
    """Gets multiline input from the user, handling the 'refine further' case."""
    if app_state.selected_task['id'] == 'refine' and app_state.last_result:
        refine_choice = input("Refine the previous result? (y/n) [y]: ").lower().strip()
        if refine_choice in ('y', ''):
            print("\n--- Using previous result as input ---")
            print(app_state.last_result)
            print("------------------------------------")
            return app_state.last_result

    prompt_msg = f"\nEnter the text for '{app_state.selected_task['name']}'"
    return input_helpers.get_multiline_input(prompt_msg)

PROMPT_MAP = {
    "refine": refine_prompts.REFINE_TEXT_PROMPT,
    "refine_presentation": refine_prompts.REFINE_PRESENTATION_PROMPT,
}

def run_model_chain(model_key, text_input, models_dict, task_id):
    """
    Runs the selected model with the given task using LangChain.
    """
    model_instance = models_dict.get(model_key)
    if not model_instance:
        return f"Error: Model '{model_key}' not found."

    try:
        output_parser = StrOutputParser()

        if task_id == "auto_translate":
            handler = TranslationHandler()
            prompt_template_str = handler.get_translation_prompt(text_input)
        else:
            prompt_template_str = PROMPT_MAP.get(task_id)

        if not prompt_template_str:
            return f"Error: Prompt for task '{task_id}' not found."

        prompt_template = ChatPromptTemplate.from_template(prompt_template_str)
        chain = prompt_template | model_instance | output_parser
        return chain.invoke({"user_text": text_input})

    except Exception as e:
        print(f"ERROR during model execution for {model_key}:")
        traceback.print_exc()
        return f"Error running model: {e}"


def handle_refine_further(app_state):
    """Asks the user if they want to refine the result further."""
    if app_state.selected_task['id'] == 'refine' and "Error" not in app_state.last_result:
        choice = input("1. Refine this result further\n2. Back to main menu\nEnter choice [2]: ").strip()
        return choice == "1"
    return False

def run_main_loop():
    """Initializes models and runs the main user interaction loop."""
    initialized_models, init_errors = initialize_all_ai_models()
    available_model_keys = sorted(initialized_models.keys())
    app_state = AppState()

    while not app_state.should_exit:
        if not app_state.selected_model:
            app_state.selected_model = select_model(available_model_keys)
            if app_state.selected_model == "exit":
                app_state.should_exit = True
                continue
            if not app_state.selected_model:
                continue  # Invalid choice, loop again

        if not app_state.selected_task:
            app_state.selected_task = select_task()
            if not app_state.selected_task:
                app_state.selected_model = None  # Go back to model selection
                continue

        user_text = get_user_input(app_state)
        if not user_text.strip():
            print("Input cannot be empty.")
            continue

        print(f"\nProcessing with '{app_state.selected_task['name']}' using model '{app_state.selected_model}'...")
        result = run_model_chain(
            app_state.selected_model, user_text, initialized_models, app_state.selected_task['id']
        )
        app_state.last_result = result

        print(f"\n--- Result from {app_state.selected_model} ---")
        print(result)
        print("----------------------------------------")

        if handle_refine_further(app_state):
            continue  # Loop to refine the same text
        else:
            # Reset for next iteration
            app_state.selected_model = None
            app_state.selected_task = None
            app_state.last_result = None
            input("Press Enter to return to the main menu...")


if __name__ == "__main__":
    try:
        run_main_loop()
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting program.")
    except Exception as e:
        print("\n--- UNHANDLED EXCEPTION IN MAIN LOOP ---")
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
    finally:
        print("\nProgram finished.")
