"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, computed_field

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_core.messages import AnyMessage


class LangGraphEngineInputState(BaseModel):
    """Base input state for LangGraph engine execution."""

    messages: Annotated[Sequence[AnyMessage], add_messages] = []
    input: BaseModel
    error_message: str = ""


class LangGraphEngineOutputState(BaseModel):
    """Base output state for LangGraph engine execution."""

    messages: Annotated[Sequence[AnyMessage], add_messages] = []
    error_message: str = ""
    output: BaseModel | None = Field(default=None)

    @computed_field
    def n_messages(self) -> int:
        """Return the number of messages in the state."""
        return len(self.messages)


class LangGraphEngineState(LangGraphEngineInputState, LangGraphEngineOutputState):
    """Combined input/output state for LangGraph engine execution."""


class LangGraphEngineContext(BaseModel):
    """Execution context for LangGraph engine runs."""

    model_endpoint_id: str = Field(
        ...,
        description="The id of the model endpoint to use",
    )
    output_model: type[BaseModel] | None = Field(default=None)
    shared_context_prompt: str
    recursion_limit: int = Field(default=15)
    tags: list[str] = Field(default_factory=list)
    agent_id: str
    forge_cycle_id: str | None = None
