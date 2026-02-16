"""
xAI model provider using official xAI SDK (gRPC).
"""

from typing import List, Dict, Any, Optional
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import Field
from models.base_model_provider import BaseModelProvider
from utils.logger import info, warning, error

try:
    import xai_sdk
    from xai_sdk.chat import system, user, assistant
except ImportError:
    xai_sdk = None


class ChatXAIGRPC(BaseChatModel):
    """
    Custom LangChain wrapper for xAI SDK (gRPC).
    """
    model_name: str
    xai_api_key: str = Field(alias="api_key")
    temperature: float = 0.7
    client: Any = None

    def __init__(self, **kwargs):
        # Ensure api_key is correctly mapped for Pydantic validation
        if "xai_api_key" in kwargs and "api_key" not in kwargs:
            kwargs["api_key"] = kwargs["xai_api_key"]
            
        super().__init__(**kwargs)
        
        if xai_sdk:
            # Initialize the xAI SDK Client (gRPC)
            self.client = xai_sdk.Client(api_key=self.xai_api_key)
        else:
            raise ImportError("xai-sdk is not installed. Please install it with: pip install xai-sdk")

    @property
    def _llm_type(self) -> str:
        return "xai-grpc"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not self.client:
            raise ValueError("xAI Client not initialized")

        # Create a new chat session for this generation
        chat = self.client.chat.create(model=self.model_name)
        
        # Convert LangChain messages to xAI SDK messages
        for msg in messages:
            if isinstance(msg, SystemMessage):
                chat.append(system(msg.content))
            elif isinstance(msg, HumanMessage):
                chat.append(user(msg.content))
            elif isinstance(msg, AIMessage):
                chat.append(assistant(msg.content))
            else:
                # Fallback for other message types
                chat.append(user(msg.content))
            
        # Sample the response from the model
        response = chat.sample()
        
        # Extract content from response
        content = response.content if hasattr(response, 'content') else str(response)
        
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])


class XAIModelProvider(BaseModelProvider):
    """
    xAI model provider using official SDK.
    """

    def __init__(self, api_key: str, provider_name: str = "xai"):
        super().__init__(api_key, provider_name)

    def _is_text_model(self, model_id: str) -> bool:
        """
        Check if the model is a text model based on its ID.
        Filters out image, vision, video, and other non-text models.
        """
        model_id_lower = model_id.lower()
        exclude_keywords = ['image', 'vision', 'video', 'audio', 'embed']
        return not any(keyword in model_id_lower for keyword in exclude_keywords)

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available xAI models using the SDK.
        """
        if not xai_sdk:
            warning("⚠️ xai-sdk not installed. Cannot fetch models via gRPC.")
            return []

        info("🔍 Fetching xAI models...")
        grok_models = []
        
        try:
            client = xai_sdk.Client(api_key=self.api_key)
            
            # Attempt to list models using the SDK
            if hasattr(client, 'models') and hasattr(client.models, 'list'):
                models = client.models.list()
                for model in models:
                    model_id = getattr(model, 'id', None)
                    if not model_id:
                        continue
                        
                    if "grok" in model_id.lower() and self._is_text_model(model_id):
                        model_def = self.create_model_definition(model_id)
                        # Override class to use our custom gRPC wrapper
                        model_def["class"] = ChatXAIGRPC
                        model_def["args"]["temperature"] = 0.7
                        grok_models.append(model_def)
            
            if grok_models:
                info(f"✅ Fetched {len(grok_models)} xAI Grok models via gRPC")
                return grok_models
                
        except Exception as e:
            pass

        # Fallback: Use OpenAI-compatible SDK for model discovery
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1")
            models_response = client.models.list()

            for model in models_response.data:
                model_id = model.id
                if model_id and "grok" in model_id.lower() and self._is_text_model(model_id):
                    model_def = self.create_model_definition(model_id)
                    grok_models.append(model_def)

            if grok_models:
                info(f"✅ Fetched {len(grok_models)} xAI Grok models via OpenAI-compatible SDK")
                return grok_models

        except Exception as e:
            warning(f"⚠️ Failed to fetch xAI models via OpenAI-compatible SDK: {e}")

        return []

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        No fallback models as we strictly use gRPC discovery.
        """
        return []

    def get_model_class(self):
        return ChatXAIGRPC

    def get_model_id_key(self) -> str:
        return "model_name"