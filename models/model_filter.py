"""
Model filtering - identifies text-based models suitable for content refinement.
"""

from config.constants import ModelFiltering
from utils.logger import info


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
