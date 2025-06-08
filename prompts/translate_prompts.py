# prompts/translate_prompts.py

TRANSLATE_EN_TO_ZH_PROMPT = (
    "You are a helpful translation assistant. Translate the following English text to Chinese. "
    "Provide only the Chinese translation.\n\n"
    "English Text:\n{user_text}\n\nChinese Translation:"
)

TRANSLATE_ZH_TO_EN_PROMPT = (
    "You are a helpful translation assistant. Translate the following Chinese text to English. "
    "Provide only the English translation.\n\n"
    "Chinese Text:\n{user_text}\n\nEnglish Translation:"
)