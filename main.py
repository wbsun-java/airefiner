import sys
import traceback

from dotenv import load_dotenv

# Load environment variables from .env file
# This should be one of the first things to run
load_dotenv()

# --- Import Custom Model Loader ---
try:
    from models import model_loader # Imports models/model_loader.py
except ImportError as e:
    print(f"FATAL ERROR: Could not import 'model_loader.py' from the 'models' directory: {e}")
    print("Make sure 'models/__init__.py' and 'models/model_loader.py' exist.")
    sys.exit(1)
except Exception as e:
    print(f"FATAL ERROR: An unexpected error occurred while importing 'model_loader.py': {e}")
    traceback.print_exc()
    sys.exit(1)

# --- Import LangChain Components ---
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError as e:
    print(f"FATAL ERROR: Could not import LangChain core components: {e}")
    print("Please ensure LangChain is installed correctly (e.g., pip install langchain-core).")
    sys.exit(1)

# --- Import Configurations, Prompts, and Utilities ---
try:
    from config import settings  # For TASKS and API key loading logic
    from prompts import refine_prompts, translate_prompts
    from utils import input_helpers # For get_multiline_input
    from utils.translation_handler import TranslationHandler  # For auto-translation
except ImportError as e:
    print(f"FATAL ERROR: Could not import necessary modules (settings, prompts, or utils): {e}")
    print("Ensure 'config/settings.py', 'prompts/*.py', and 'utils/input_helpers.py' exist with their __init__.py files.")
    sys.exit(1)


# --- Model Initialization Wrapper ---
# ... (This part of the code remains unchanged) ...
def initialize_all_ai_models():
    """
    Initializes AI models by calling the main initializer function from model_loader.py.
    """
    print("Attempting to initialize AI models via models/model_loader.py...")
    initialized_models_dict = {}
    initialization_errors_dict = {}

    try:
        if hasattr(model_loader, 'initialize_models'):
            initialized_models_dict, initialization_errors_dict = model_loader.initialize_models()
        else:
            error_msg = "ERROR: 'models/model_loader.py' does not have a recognized model initialization function (e.g., 'initialize_models')."
            print(error_msg)
            initialization_errors_dict["model_loader.py_interface"] = error_msg
            return {}, initialization_errors_dict

        if not initialized_models_dict and not initialization_errors_dict:
            print("Warning: model_loader.py's initialization function returned no models and no errors. "
                  "Check model_loader.py implementation and API key availability in .env (loaded by config/settings.py).")
            initialization_errors_dict[
                "model_loader_empty_return"] = "No models or specific errors returned from model_loader.py."
        elif not initialized_models_dict:
            print("No models were successfully initialized by model_loader.py.")

    except AttributeError as e:
        error_msg = f"ERROR: 'models/model_loader.py' seems to be missing an expected attribute or function: {e}"
        print(error_msg)
        initialization_errors_dict["model_loader.py_interface_attr"] = error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while trying to load models from model_loader.py: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        initialization_errors_dict["model_loader.py_execution"] = error_msg

    return initialized_models_dict, initialization_errors_dict

# --- Model Execution ---
PROMPT_MAP = {
    "refine": refine_prompts.REFINE_TEXT_PROMPT,
    "refine_presentation": refine_prompts.REFINE_PRESENTATION_PROMPT,
    # auto_translate will be handled dynamically by TranslationHandler
}

def run_model_chain(model_key, text_input, models_dict, task_id):
    """
    Runs the selected model with the given task using LangChain.
    """
    print(f"\nAttempting to run model '{model_key}' for task '{task_id}'...")
    model_instance = models_dict.get(model_key)

    if not model_instance:
        return f"Error: Model '{model_key}' not found in initialized models."

    print(f"DEBUG: Model instance for '{model_key}': {type(model_instance)}")

    try:
        output_parser = StrOutputParser()

        # Handle auto-translation task
        if task_id == "auto_translate":
            handler = TranslationHandler()
            translation_info = handler.determine_translation_direction(text_input)

            # Show translation summary
            summary = handler.get_translation_summary(translation_info, text_input)
            print(f"\n{summary}")

            # Use the dynamically determined prompt and task
            actual_task_id = translation_info['task_id']

            if actual_task_id == 'zh_to_en':
                prompt_template_str = translate_prompts.TRANSLATE_ZH_TO_EN_PROMPT
            elif actual_task_id == 'en_to_zh':
                prompt_template_str = translate_prompts.TRANSLATE_EN_TO_ZH_PROMPT
            else:
                # Fallback to refine if language detection failed
                prompt_template_str = refine_prompts.REFINE_TEXT_PROMPT

            print(f"Using task: {actual_task_id}")
        else:
            # Regular tasks
            prompt_template_str = PROMPT_MAP.get(task_id)

        if not prompt_template_str:
            return f"Error: Unknown task_id '{task_id}' for model '{model_key}'. No chain defined."

        if prompt_template_str:
            prompt_template = ChatPromptTemplate.from_template(prompt_template_str)
            chain = prompt_template | model_instance | output_parser
            result = chain.invoke({"user_text": text_input})  # Ensure the placeholder in the prompt is "user_text"
            return result
        else:
            return f"Error: Prompt template not found for task_id '{task_id}'."


    except Exception as e:
        print(f"ERROR during model execution for {model_key}, task {task_id}:")
        traceback.print_exc()
        return f"Error running model {model_key} for task {task_id}: {e}"

# --- Main Application Loop ---
# ... (run_main_loop and __main__ parts remain unchanged) ...
def run_main_loop():
    """Initializes models and runs the main user interaction loop."""

    initialized_models, init_errors = initialize_all_ai_models()

    if not initialized_models:
        print("\n--- FATAL ERROR ---")
        print("No AI models were successfully initialized.")
        if init_errors:
            print("The following errors occurred during initialization:")
            for model_name_key, error_msg in init_errors.items():
                print(f"- {model_name_key}: {error_msg}")
        else:
            print("No specific errors were reported, but initialization failed.")
        sys.exit(1)

    available_model_keys = sorted(list(initialized_models.keys()))

    print(f"\n--- Successfully Initialized Models ({len(available_model_keys)} available) ---")
    current_provider_group = None
    model_display_number = 1
    for key in available_model_keys:
        provider_name = key.split('/')[0] # Extract provider name (e.g., "openai")
        if provider_name != current_provider_group:
            if current_provider_group is not None: # Don't print separator before the first group
                print("---") # Separator line
            current_provider_group = provider_name
            # Optionally, you could print a header for the new group:
            # print(f"\n# {provider_name.capitalize()} Models:")
        print(f"{model_display_number}. {key}")
        model_display_number += 1

    if init_errors:
        print("\n--- Initialization Warnings ---")
        print("Some models may have failed to initialize (check logs above). They will not be available if not listed above.")
        for model_name_key, error_msg in init_errors.items():
            if model_name_key not in initialized_models:
                 print(f"- {model_name_key}: {error_msg}")

    last_refinement_result = None
    refine_further_active = False
    selected_key = None
    selected_task_id = None
    selected_task_info = None

    while True:
        print("\n----------------------------------------")

        if not refine_further_active:
            print("Select a model to use:")
            current_provider_group_select = None # For grouping in selection
            model_select_number = 1 # For numbering in selection
            for key_option in available_model_keys:
                provider_name_select = key_option.split('/')[0]
                if provider_name_select != current_provider_group_select:
                    if current_provider_group_select is not None:
                        print("---") # Separator line
                    current_provider_group_select = provider_name_select
                    # Optionally, print a header for the new group:
                    # print(f"\n# {provider_name_select.capitalize()} Models:")
                print(f"{model_select_number}. {key_option}")
                model_select_number += 1
            print("0. Exit")

            choice = input("Enter model choice number: ").strip()
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    print("Exiting.")
                    break
                if 1 <= choice_num <= len(available_model_keys):
                    selected_key = available_model_keys[choice_num - 1]
                    print(f"\n>>> You have selected model: {selected_key} <<<")
                    last_refinement_result = None
                else:
                    print("Invalid model choice number.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            print("\nSelect a task to perform:")
            # Use TASKS from settings module
            for task_num_str, task_info_loop in settings.TASKS.items():
                print(f"{task_num_str}. {task_info_loop['name']}")
            print("0. Back to model selection")

            task_choice = input("Enter task choice number: ").strip()
            if task_choice == "0":
                last_refinement_result = None
                continue

            selected_task_info = settings.TASKS.get(task_choice)
            if not selected_task_info:
                print("Invalid task choice number.")
                last_refinement_result = None
                continue

            selected_task_id = selected_task_info['id']
            # For the new task "refine_presentation", it doesn't have special "refine_further_active" logic like "refine"
            # So if "refine_presentation" is selected, last_refinement_result should also be cleared
            if selected_task_id != "refine":
                last_refinement_result = None
        else:  # refine_further_active is True
            print(f"\nContinuing refinement with model '{selected_key}'...")
            if selected_task_id != "refine":  # This should only happen in the refine task
                 print("Error: refine_further_active mode but task is not 'refine'. Resetting.")
                 refine_further_active = False
                 last_refinement_result = None
                 continue

        user_text = ""
        if refine_further_active:  # This block is only for the "refine" task's follow-up
            if last_refinement_result:
                user_text = last_refinement_result
                print("\n--- Using previous refinement result as input ---")
                print(user_text)
                print("-------------------------------------------------")
                refine_further_active = False  # Reset after using it
            else:
                print("Error: refine_further_active is True, but no previous result. Please provide input.")
                refine_further_active = False  # Reset as it's an error state

        if not user_text:  # If not continuing a "refine" task or if it's a new task
            use_previous_refinement_for_input = False
            # Special logic for the "refine" task, asking whether to use the previous result
            if selected_task_id == "refine" and last_refinement_result:
                refine_choice = input(f"Do you want to refine the previous result? (y/n) [y]: ").lower().strip()
                if refine_choice == "" or refine_choice == "y":
                    user_text = last_refinement_result
                    print("\n--- Using previous refinement result as input ---")
                    print(user_text)
                    print("-------------------------------------------------")
                    use_previous_refinement_for_input = True
                else:
                    last_refinement_result = None  # User chose not to use it

            if not user_text:  # If still no user_text (e.g. new task, or refine task where user said 'n')
                if not use_previous_refinement_for_input and selected_task_id == "refine":
                    last_refinement_result = None  # Ensure it's cleared if not used for refine
                input_prompt_msg = f"\nEnter the text for '{selected_task_info['name']}' using model '{selected_key}'."
                user_text = input_helpers.get_multiline_input(input_prompt_msg)

        if not user_text.strip():  # Check after all input attempts
            print("Input cannot be empty.")
            last_refinement_result = None  # Clear if input is empty
            refine_further_active = False  # Reset
            continue

        print(f"\nProcessing with '{selected_task_info['name']}' using model '{selected_key}'...")
        result = run_model_chain(selected_key, user_text, initialized_models, selected_task_id)

        print(f"\n--- Result for '{selected_task_info['name']}' from {selected_key} ---")
        print(result)
        print("----------------------------------------")

        # Special follow-up logic for the "refine" task
        if selected_task_id == "refine":
            if "Error running model" not in result and "Error: Model" not in result:
                last_refinement_result = result  # Save for potential next refinement
                continue_choice = input("1. Refine this result further (using same model).\n"
                                        "2. Back to main menu (select model/task).\n"
                                        "Enter choice [2]: ").strip()
                if continue_choice == "1":
                    refine_further_active = True
                    # selected_key and selected_task_id remain unchanged
                    continue  # Go to the top of the loop, refine_further_active will be true
            else:  # Error occurred
                last_refinement_result = None
            refine_further_active = False  # Reset if not continuing or if error
        else:  # For "en_to_zh", "zh_to_en", "refine_presentation"
            last_refinement_result = None  # These tasks don't have a direct "refine further" state
            refine_further_active = False
            input("Press Enter to return to the main menu...")
        # Loop will restart, refine_further_active will be false, prompting for model/task selection

# --- Main Execution Guard ---
if __name__ == "__main__":
    try:
        run_main_loop()
    except Exception as e:
        print("\n--- UNHANDLED EXCEPTION IN MAIN LOOP ---")
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
    finally:
        print("\nProgram finished.")