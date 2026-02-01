from typing import Any

class BaseMessage:
    content: str
    type: str
    response_metadata: dict[str, Any]
    tool_calls: list[dict[str, Any]] | None

    def __init__(self, content: str = ..., **kwargs: Any) -> None: ...

class HumanMessage(BaseMessage):
    type: str

class AIMessage(BaseMessage):
    type: str
    tool_calls: list[dict[str, Any]] | None

    def __init__(self, content: str = ..., *, tool_calls: list[dict[str, Any]] | None = ..., **kwargs: Any) -> None: ...

class ToolMessage(BaseMessage):
    type: str
    tool_call_id: str

    def __init__(self, content: str = ..., *, tool_call_id: str = ..., name: str | None = ..., **kwargs: Any) -> None: ...

class SystemMessage(BaseMessage):
    type: str

class ToolCall(dict[str, Any]):
    def __init__(self, *, name: str, args: dict[str, Any], id: str) -> None: ...
type AnyMessage = HumanMessage | AIMessage | ToolMessage | SystemMessage
