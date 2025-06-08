# prompts/refine_prompts.py

REFINE_TEXT_PROMPT = (
    "You are a helpful assistant that refines and improves text. "
    "Please refine the following text, making it clearer, more concise, and grammatically correct. "
    "Do not add any conversational fluff, just provide the refined text.\n\n"
    "Original Text:\n{user_text}\n\nRefined Text:"
)