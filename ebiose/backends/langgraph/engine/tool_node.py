"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal, cast

from langchain_core.messages import ToolMessage
from loguru import logger
from pydantic import BaseModel, Field, computed_field

from ebiose.backends.langgraph.engine.states import (
    LangGraphEngineInputState,
    LangGraphEngineOutputState,
)
from ebiose.core.engines.graph_engine.nodes.node import BaseNode

if TYPE_CHECKING:
    import builtins


class InputState(LangGraphEngineInputState):
    """Input state for tool execution nodes."""


class OutputState(LangGraphEngineOutputState):
    """Output state for tool execution nodes."""


class LangGraphToolNode(BaseNode):
    """LangGraph node that invokes tools from tool-call messages."""

    tools: list = Field(default_factory=list)
    type: Literal["LLMNode"] = "LLMNode"
    purpose: str = Field(..., description="An explanation of what the node is used for")
    prompt: str = Field(
        ...,
        description="el",
    )
    input_state_model: builtins.type[BaseModel] = InputState
    output_state_model: builtins.type[BaseModel] = OutputState

    @computed_field
    def tools_by_name(self) -> dict[str, Any]:
        """Return a dictionary mapping tool names to their respective Tool objects."""
        return {tool.name: tool for tool in self.tools}

    async def call_node(
        self,
        state: BaseModel | dict,
        config: BaseModel | None = None,
    ) -> dict:
        """Execute tools from the last message and return tool responses.

        Args:
            state: Input state containing messages with tool calls.
            config: Optional runtime configuration (unused).

        Returns:
            A dictionary with tool response messages.

        Raises:
            ValueError: If execution fails unexpectedly.

        """
        _ = config  # Unused parameter
        try:
            outputs: list[ToolMessage] = []
            # Handle both dict and structured state
            if isinstance(state, dict):
                messages = state.get("messages", [])
            else:
                # Assume BaseModel with messages attribute
                messages = getattr(state, "messages", [])
            last_message = messages[-1] if messages else None
            tool_calls = getattr(last_message, "tool_calls", []) if last_message else []

            for tool_call in tool_calls:
                if (
                    isinstance(tool_call, dict)
                    and "name" in tool_call
                    and "args" in tool_call
                ):
                    try:
                        tool_name = str(tool_call["name"])
                        tools_dict = cast("dict[str, Any]", self.tools_by_name)
                        if tool_name in tools_dict:
                            tool_result = tools_dict[tool_name].invoke(
                                tool_call["args"],
                            )
                            outputs.append(
                                ToolMessage(
                                    content=json.dumps(tool_result),
                                    name=tool_call.get("name", ""),
                                    tool_call_id=tool_call.get("id", ""),
                                ),
                            )
                    except (
                        ValueError,
                        TypeError,
                        RuntimeError,
                        KeyError,
                        AttributeError,
                        ImportError,
                    ) as e:
                        logger.warning(
                            f"Failed to invoke tool {tool_call.get('name', 'unknown')}: {e}",
                        )
                        continue
        except Exception as e:
            logger.debug(f"Error when calling node {self.name}: {e!s}")
            msg = "Failed during call to a tool Node."
            raise ValueError(msg) from e
        else:
            return {"messages": outputs}
