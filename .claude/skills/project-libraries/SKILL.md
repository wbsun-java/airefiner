---
name: project-libraries
description: Use when working with any provider SDK code in this project (anthropic, openai, google-genai, groq, xai-sdk). Check reference.md before using Context7 or training knowledge for API patterns.
---

# Project Libraries Reference

## Rule: reference.md first, Context7 never (for these packages)

When you need API patterns for any of the 5 provider SDKs in this project:

1. **Read `reference.md`** in this directory — it contains the exact patterns used in this codebase.
2. **Do not call Context7** for these packages. The reference is derived directly from the working provider files.
3. **Do not rely solely on training knowledge** for xai-sdk — it is niche and training coverage is sparse.

## When reference.md is stale

The reference was written against these version floors:

| Package | Floor |
|---|---|
| anthropic | 0.86 |
| openai | 2.30 |
| google-genai | 1.69 |
| groq | 1.1 |
| xai-sdk | 1.11 |

If `requirements.txt` shows a **major version bump** from any of the above, the reference may be outdated. In that case, use Context7 for the specific package that changed — not for all of them.

## Packages that never need a lookup

`python-dotenv`, `requests`, `langdetect` — rely on training knowledge.
