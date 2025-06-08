import requests
import warnings
from typing import List, Optional, Any, Dict, Iterator

# LangChain Core types
try:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
    from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
    from langchain_core.callbacks import CallbackManagerForLLMRun
except ImportError:
    warnings.warn("Using fallback imports for older LangChain. Consider upgrading LangChain.")
    from langchain.chat_models.base import BaseChatModel # type: ignore
    from langchain.schema import BaseMessage, AIMessage, HumanMessage, SystemMessage, ChatResult, ChatGeneration # type: ignore
    from langchain.callbacks.manager import CallbackManagerForLLMRun # type: ignore
    try:
        from langchain_core.outputs import ChatGenerationChunk # type: ignore
    except ImportError:
        ChatGenerationChunk = None


class CustomGrokChatModel(BaseChatModel):
    """
    Custom implementation for interacting with a specific, speculative
    Grok API endpoint using the requests library.
    """
    api_key: str
    model: str
    api_endpoint: str = "https://api.x.ai/v1/chat/completions"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.api_key:
             raise ValueError("xAI API key must be provided.")
        # warnings.warn(
        #     "Using speculative CustomGrokChatModel. API behavior is unknown.",
        #     UserWarning
        # )

    @property
    def _llm_type(self) -> str:
        return "grok-chat-custom-requests-final"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "api_endpoint": self.api_endpoint,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        formatted_messages = []
        for msg in messages:
            role: Optional[str] = None
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            if role and hasattr(msg, 'content'):
                formatted_messages.append({"role": role, "content": str(msg.content)})
            elif hasattr(msg, 'content'):
                 warnings.warn(f"Unknown message type {type(msg)}, attempting to send as 'user'.")
                 formatted_messages.append({"role": "user", "content": str(msg.content)})
            else:
                warnings.warn(f"Ignoring message without role or content: {msg}")

        if not formatted_messages:
            raise ValueError("Cannot send request with no valid messages.")

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
        }
        if self.temperature is not None:
             payload["temperature"] = self.temperature
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        if stop:
            payload["stop"] = stop
        payload.update(kwargs)

        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=90
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.Timeout as e:
            raise ConnectionError(f"Timeout connecting to Grok API at {self.api_endpoint}: {e}") from e
        except requests.exceptions.ConnectionError as e:
            if 'SSL' in str(e) or 'certificate verify failed' in str(e):
                 raise ConnectionError(
                     f"SSL Error connecting to Grok API at {self.api_endpoint}. Original error: {e}"
                 ) from e
            raise ConnectionError(f"Network connection error to Grok API at {self.api_endpoint}: {e}") from e
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            try:
                error_body = e.response.json()
                error_detail = error_body.get("error", {}).get("message", e.response.text)
            except requests.exceptions.JSONDecodeError:
                error_detail = e.response.text
            if status_code == 401:
                raise ValueError(f"[Grok API Auth Error 401] Invalid API key? Detail: {error_detail}") from e
            # Add other status code handling as in your original file
            else:
                raise Exception(f"[Grok API HTTP Error {status_code}] Detail: {error_detail}") from e
        except requests.exceptions.JSONDecodeError as e:
             raise ValueError(f"Failed to decode JSON response from Grok API. Response text: {getattr(e.response, 'text', 'N/A')}") from e
        except Exception as e:
            raise Exception(f"An unexpected error occurred during Grok API call: {e}") from e

        try:
            choice = result["choices"][0]
            message_data = choice["message"]
            generated_content = message_data.get("content")
            if generated_content is None:
                 raise ValueError("API response choice message is missing 'content'.")
            role = message_data.get("role", "assistant")
            if role != "assistant":
                warnings.warn(f"Received unexpected role '{role}' in Grok API response.")
            usage_info = result.get("usage")
            generation_info = {"finish_reason": choice.get("finish_reason")}
            if usage_info:
                generation_info["usage"] = usage_info
            generation = ChatGeneration(
                message=AIMessage(content=str(generated_content)), # Ensure content is string
                generation_info=generation_info
            )
            return ChatResult(generations=[generation], llm_output=usage_info if usage_info else None)
        except (KeyError, IndexError, TypeError, AttributeError) as e:
             raise ValueError(f"Failed to parse Grok API response. Unexpected format. Received: {result}. Error: {e}") from e

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        warnings.warn("Streaming not implemented for CustomGrokChatModel.", UserWarning)
        raise NotImplementedError("Streaming is not supported by this custom Grok model implementation.")
