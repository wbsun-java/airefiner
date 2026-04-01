"""
xAI model provider - fetches and manages xAI Grok models.
"""

from typing import List, Dict, Any, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import PrivateAttr

from models.base_model_provider import BaseModelProvider
from utils.logger import info, error

try:
    import xai_sdk
    from xai_sdk.chat import system, user, assistant
except ImportError:
    xai_sdk = None


class ChatXAI(BaseChatModel):
    """LangChain wrapper for the xAI SDK (gRPC)."""

    model_name: str
    xai_api_key: str
    temperature: float = 0.7

    _client: Any = PrivateAttr(default=None)

    @property
    def _llm_type(self) -> str:
        return "xai"

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = xai_sdk.Client(api_key=self.xai_api_key)
        return self._client

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        client = self._get_client()

        xai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                xai_messages.append(system(msg.content))
            elif isinstance(msg, AIMessage):
                xai_messages.append(assistant(msg.content))
            else:
                xai_messages.append(user(msg.content))

        chat = client.chat.create(model=self.model_name, messages=xai_messages)
        response = chat.sample()
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response.content))])


class XAIModelProvider(BaseModelProvider):
    """xAI model provider using the official xAI SDK."""

    def __init__(self, api_key: str, provider_name: str = "xai"):
        super().__init__(api_key, provider_name)

    def get_model_class(self):
        return ChatXAI

    def get_model_id_key(self) -> str:
        return "model_name"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Fetch available xAI language models using the xAI SDK."""
        from models.model_filter import is_text_model, deduplicate_models

        try:
            if xai_sdk is None:
                raise ImportError("xai-sdk package not available")

            client = xai_sdk.Client(api_key=self.api_key)
            model_ids = [m.name for m in client.models.list_language_models()
                         if getattr(m, "name", None) and is_text_model(m.name, 'xai')]
            models = [self.create_model_definition(m) for m in deduplicate_models(model_ids)]

            info(f"Fetched {len(models)} xAI models dynamically")
            return models

        except Exception as e:
            error(f"Failed to fetch xAI models: {e}")
            return self.get_fallback_models()

    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """Fallback xAI models if dynamic fetching fails."""
        from models.model_filter import is_text_model

        model_ids = ["grok-4-0709", "grok-3", "grok-3-mini"]
        return [self.create_model_definition(m) for m in model_ids
                if is_text_model(m, 'xai')]
