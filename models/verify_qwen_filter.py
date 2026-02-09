
import sys
import os

# Add parent directory to path to allow importing from models package correctly 
# if running as a script from models/ directory without package context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.qwen_provider import QwenModelProvider
except ImportError:
    # Fallback if running from root context
    try:
        from qwen_provider import QwenModelProvider
    except ImportError:
        print("Could not import QwenModelProvider")
        sys.exit(1)

from typing import List, Dict, Any

# Mock data
model_ids = [
    "qwen-plus-2025-01-25",
    "qwen-plus-2025-12-01",
    "qwen-plus", 
    "qwen-max-2025-01-25",
    "qwen-max-latest"
]

# Convert to list of dictionaries as expected by the provider
# Note: The provider expects 'args' -> 'model_name'
models = [{"id": mid, "args": {"model_name": mid}} for mid in model_ids]

print("Original models:")
for m in models:
    print(f"- {m['args']['model_name']}")

try:
    # Initialize provider (api_key is required but not used for this method test)
    provider = QwenModelProvider(api_key="mock_key")
    
    # Test internal method directly
    filtered = provider._filter_dated_models(models)
    
    print("\nFiltered models:")
    for m in filtered:
        print(f"- {m['args']['model_name']}")
        
    # Validation
    expected = ["qwen-plus-2025-12-01", "qwen-plus", "qwen-max-2025-01-25", "qwen-max-latest"]
    filtered_ids = sorted([m['args']['model_name'] for m in filtered])
    expected_ids = sorted(expected)
    
    if filtered_ids == expected_ids:
        print("\n✅ Verification SUCCESS: Logic matches expectation.")
    else:
        print(f"\n❌ Verification FAILED: Expected {expected_ids}, got {filtered_ids}")

except Exception as e:
    print(f"\n❌ Verification ERROR: {e}")
