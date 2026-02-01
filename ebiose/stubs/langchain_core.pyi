# Type stubs for langchain_core
from typing import Any, Protocol

class BaseMessage:
    content: str
    type: str

class HumanMessage(BaseMessage):
    type: str = "human"

class AIMessage(BaseMessage):
    type: str = "ai"
    tool_calls: list[dict[str, Any]] | None = None

class ToolMessage(BaseMessage):
    type: str = "tool"
    tool_call_id: str

class SystemMessage(BaseMessage):
    type: str = "system"

type AnyMessage = HumanMessage | AIMessage | ToolMessage | SystemMessage

class Runnable(Protocol):
    def invoke(self, input: Any) -> Any: ...

class BaseChatModel(Runnable): ...

class ChatOpenAI(BaseChatModel):
    def __init__(
        self,
        openai_api_key: str | None = None,
        openai_api_base: str | None = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> None: ...

class AzureChatOpenAI(BaseChatModel):
    def __init__(
        self,
        azure_endpoint: str | None = None,
        azure_deployment: str = "",
        api_key: str | None = None,
        api_version: str = "2023-12-01-preview",
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> None: ...
