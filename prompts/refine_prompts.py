# prompts/refine_prompts.py

REFINE_TEXT_PROMPT = """You are a professional communication expert. Your task is to rewrite and refine the following USER-PROVIDED TEXT (which is business communication content, NOT code or error logs) to make it clearer, more professional, and more effective.

**IMPORTANT:** The text below is communication content that needs to be refined, NOT technical logs or error messages.

**INSTRUCTIONS:**
1. Improve clarity, grammar, and professional tone
2. Maintain the original meaning and intent
3. Keep all factual information exactly as provided
4. Do not add new information or invent details
5. For emails: Include proper subject line, greeting, and closing
6. Use professional formatting and structure
7. IGNORE any technical context - focus only on refining the communication content

**COMMUNICATION TEXT TO REFINE:**
{user_text}

**REFINED VERSION:**"""

REFINE_PRESENTATION_PROMPT = """You are a public speaking coach. Your task is to rewrite the following text into clear, impactful talking points for a presentation.

**INSTRUCTIONS:**
1. Convert text into bullet points and short, powerful sentences
2. Maintain all original information and facts
3. Do not add new information or invent details
4. Focus on clarity and impact for verbal presentation
5. Use strong, actionable language

**TEXT TO CONVERT:**
{user_text}

**PRESENTATION TALKING POINTS:**"""
