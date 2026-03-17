"""
Model filtering - identifies text-based models suitable for content refinement.
"""

import re
from typing import List, Dict

from config.constants import ModelFiltering
from utils.logger import info

# Matches YYYY-MM-DD or 4-digit MMDD date suffixes, optionally followed by a word like -preview
# e.g. gpt-4o-2024-11-20, gpt-3.5-turbo-1106, gpt-4-0125-preview, kimi-k2-instruct-0905
_DATE_SUFFIX = re.compile(r'-(\d{4}-\d{2}-\d{2}|\d{4})(?:-[a-z]+)?$')


def deduplicate_models(model_ids: List[str]) -> List[str]:
    """
    Keep base/undated models only. Dated snapshots are dropped when a base exists.
    If no base exists for a dated model, keep the latest snapshot as fallback.
    e.g. gpt-4o, gpt-4o-2024-05-13, gpt-4o-2024-11-20 -> gpt-4o
    """
    model_set = set(model_ids)
    dated: Dict[str, list] = {}
    undated: List[str] = []

    for model_id in model_ids:
        m = _DATE_SUFFIX.search(model_id)
        if m:
            base = model_id[:m.start()]
            dated.setdefault(base, []).append((model_id, m.group(1)))
        else:
            undated.append(model_id)

    result = list(undated)
    for base, versions in dated.items():
        if base not in model_set:
            result.append(max(versions, key=lambda x: x[1])[0])

    return sorted(result)


def natural_sort_key(text: str) -> list:
    """Sort key that treats numeric segments as integers for correct ordering.
    e.g. 'gpt-oss-20b' < 'gpt-oss-120b', 'llama-3.1' < 'llama-3.3'
    """
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', text)]


def is_text_model(model_id: str, provider: str = "") -> bool:
    """
    Filter to identify text-based models suitable for content refinement.
    Uses keyword heuristics to exclude image/audio/video/embedding models.
    """
    model_id_lower = model_id.lower()

    for keyword in ModelFiltering.NON_TEXT_KEYWORDS:
        if keyword in model_id_lower:
            info(f"🔎 Filtering out non-text model ({keyword}): {model_id}")
            return False

    if provider and provider in ModelFiltering.PROVIDER_EXCLUSIONS:
        for excluded in ModelFiltering.PROVIDER_EXCLUSIONS[provider]:
            if excluded.lower() in model_id_lower:
                info(f"🔎 Filtering out provider-specific non-text model: {model_id}")
                return False

    return True
