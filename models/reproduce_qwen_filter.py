
import re
from typing import List, Dict, Any

# Mock data
model_ids = [
    "qwen-flash",
    "qwen-max-2025-01-25",
    "qwen-max-latest", 
    "qwen-plus-2025-01-25",
    "qwen-plus-2025-12-01",
    "qwen-plus"
]

# Convert to list of dictionaries as expected by the provider
models = [{"id": mid, "owned_by": "alibaba"} for mid in model_ids]

def filter_dated_models(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out older dated versions of models, keeping only the latest one per base model.
    """
    dated_models_map = {}
    other_models = []
    
    date_pattern = re.compile(r"^(.*)-(\d{4}-\d{2}-\d{2})$")

    for model in models:
        mid = model.get("id", "")
        match = date_pattern.match(mid)
        if match:
            base_name = match.group(1)
            date_str = match.group(2)
            if base_name not in dated_models_map:
                dated_models_map[base_name] = []
            dated_models_map[base_name].append((date_str, model))
        else:
            other_models.append(model)
            
    final_models = []
    final_models.extend(other_models)
    
    for base_name, variations in dated_models_map.items():
        variations.sort(key=lambda x: x[0], reverse=True)
        # Keep the latest
        _, best_model = variations[0]
        final_models.append(best_model)
        
    final_models.sort(key=lambda x: x["id"])
    return final_models

if __name__ == "__main__":
    filtered = filter_dated_models(models)
    print(f"Original: {[m['id'] for m in models]}")
    print(f"Filtered: {[m['id'] for m in filtered]}")
