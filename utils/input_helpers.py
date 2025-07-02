# utils/input_helpers.py

from config.constants import InputConfig

def get_multiline_input(prompt_message: str) -> str:
    """Helper function to get multi-line input from the user."""
    print(prompt_message)
    print(f"Enter line by line. Type '{InputConfig.MULTILINE_TERMINATOR}' on a new line when you are finished:")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().lower() == InputConfig.MULTILINE_TERMINATOR.lower():
                break
            lines.append(line)
        except EOFError: # Handle Ctrl+D or Ctrl+Z
            break
    return "\n".join(lines).strip()