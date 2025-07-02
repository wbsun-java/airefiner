# prompts/refine_prompts.py

REFINE_TEXT_PROMPT = """You are a professional communication expert. Refine the following business communication content to make it clearer, more professional, and more effective.

**OUTPUT FORMAT REQUIREMENTS:**
- Provide ONLY the refined version first
- Do NOT explain your thinking process or reasoning
- Do NOT provide commentary before the refined text
- After the refined text, optionally add 2-3 key improvement bullet points

**INSTRUCTIONS:**
1. Improve clarity, grammar, and professional tone
2. Maintain the original meaning and intent exactly
3. Keep all factual information as provided
4. Do not add new information or invent details
5. For emails: Include proper subject line, greeting, and closing
6. Use professional formatting and structure

**TEXT TO REFINE:**
{user_text}

**REFINED VERSION:**
[Provide the refined text here immediately, without explanation]

**KEY IMPROVEMENTS:**
[Optional: List 2-3 main improvements made]"""

REFINE_PRESENTATION_PROMPT = """You are a public speaking coach. Convert the following text into clear, impactful talking points for a presentation.

**OUTPUT FORMAT REQUIREMENTS:**
- Provide ONLY the presentation talking points first
- Do NOT explain your approach or reasoning
- Do NOT provide commentary before the talking points
- After the talking points, optionally add 2-3 key presentation improvements made

**INSTRUCTIONS:**
1. Convert text into bullet points and short, powerful sentences
2. Maintain all original information and facts exactly
3. Do not add new information or invent details
4. Focus on clarity and impact for verbal presentation
5. Use strong, actionable language
6. Structure for easy verbal delivery

**TEXT TO CONVERT:**
{user_text}

**PRESENTATION TALKING POINTS:**
[Provide the talking points here immediately, without explanation]

**KEY IMPROVEMENTS:**
[Optional: List 2-3 main presentation enhancements made]"""
