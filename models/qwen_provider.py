"""
Qwen model provider using native Alibaba Cloud DashScope API.
"""

import requests
from typing import List, Dict, Any, Optional

from models.base_model_provider import BaseModelProvider
from config.constants import ModelFiltering
from utils.logger import info, warning, error

# Define a wrapper class to handle Qwen's API key while using ChatOpenAI
try:
    from langchain_openai import ChatOpenAI

    class QwenChatWrapper(ChatOpenAI):
        """
        A wrapper for ChatOpenAI to use Qwen's compatible API.
        It explicitly accepts 'qwen_api_key' and passes it to the underlying
        ChatOpenAI class as 'openai_api_key'.
        """
        def __init__(self, qwen_api_key: str = None, **kwargs: Any):
            if not qwen_api_key:
                raise ValueError("Qwen provider requires a 'qwen_api_key', but none was provided.")
            
            # The super class (ChatOpenAI) always expects 'openai_api_key'.
            # We pass the qwen_api_key to it under that name.
            super().__init__(openai_api_key=qwen_api_key, **kwargs)

except ImportError:
    # If langchain_openai is not installed, create a dummy class
    QwenChatWrapper = None


class QwenModelProvider(BaseModelProvider):
    """
    Qwen model provider using native Alibaba Cloud DashScope API.
    """

    def __init__(self, api_key: str, provider_name: str = "qwen"):
        """
        Initialize the Qwen model provider.
        
        Args:
            api_key: Qwen API key for authentication
            provider_name: Name of the provider (defaults to 'qwen')
        """
        super().__init__(api_key, provider_name)
        self.compatible_mode_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available Qwen models from Alibaba Cloud DashScope compatible mode API.
        
        Returns:
            List of model dictionaries with standardized format
        """
        info("🔍 Fetching Qwen models from DashScope compatible mode API...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.compatible_mode_url}/models", 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            warning(f"⚪ Failed to fetch Qwen models: {e}")
            return []

        data = response.json()
        qwen_models = []
        
        if 'data' in data:
            for model_info in data['data']:
                model_id = model_info.get('id', '')
                
                if self.is_text_model(model_id):
                    model_def = self.create_model_definition(model_id)
                    # We do not add the API key here; the legacy model loader injects it.
                    # The QwenChatWrapper is designed to handle the injected key.
                    model_def["args"].update({
                        "model_name": model_id,
                        "base_url": self.compatible_mode_url
                    })
                    qwen_models.append(model_def)
        
        info(f"✅ Fetched {len(qwen_models)} Qwen models dynamically")
        return qwen_models

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Get fallback Qwen models when API fetching fails.
        
        Returns:
            An empty list, as dynamic fetching is preferred.
        """
        return []

    def get_model_class(self):
        """
        Get the LangChain model class for Qwen provider.
        
        Returns:
            The QwenChatWrapper class that handles API key mapping.
        """
        if QwenChatWrapper is None:
            warning("langchain_openai is not installed. Please install it to use Qwen models.")
        return QwenChatWrapper

    def get_model_id_key(self) -> str:
        """
        Get the parameter name used for model ID in the constructor.
        
        Returns:
            Parameter name 'model_name'
        """
        return "model_name"

    def is_text_model(self, model_id: str) -> bool:
        """
        Check if a model is suitable for text processing.
        
        Args:
            model_id: The model identifier to evaluate
            
        Returns:
            bool: True if the model appears to be suitable for text processing
        """
        model_id_lower = model_id.lower()

        # Common non-text keywords
        non_text_keywords = ModelFiltering.NON_TEXT_KEYWORDS.copy()

        # Check common non-text keywords
        for keyword in non_text_keywords:
            if keyword in model_id_lower:
                info(f"🔎 Filtering out non-text model ({keyword}): {model_id}")
                return False

        # Check for text model indicators
        text_indicators = ModelFiltering.TEXT_INDICATORS + ['qwen']
        has_text_indicator = any(indicator in model_id_lower for indicator in text_indicators)

        if not has_text_indicator:
            info(f"🔎 Model may not be text-focused (no text indicators): {model_id}")
            return False

        return True
