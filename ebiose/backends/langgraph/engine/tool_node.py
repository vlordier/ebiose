"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field, computed_field

from ebiose.backends.langgraph.engine.states import (
    LangGraphEngineInputState,
    LangGraphEngineOutputState,
)
from ebiose.core.engines.graph_engine.nodes.node import BaseNode


class InputState(LangGraphEngineInputState):
    pass


class OutputState(LangGraphEngineOutputState):
    pass


class LangGraphToolNode(BaseNode):
    tools: list = Field(default_factory=list)
    type: Literal["LLMNode"] = "LLMNode"
    purpose: str = Field(..., description="An explanation of what the node is used for")
    prompt: str = Field(
        ...,
        description="el",
    )
    input_state_model: type[BaseModel] = InputState
    output_state_model: type[BaseModel] = OutputState

    @computed_field
    def tools_by_name(self) -> dict[str, Any]:
        """Returns a dictionary mapping tool names to their respective Tool objects."""
        return {tool.name: tool for tool in self.tools}

    async def call_node(
        self,
        state: BaseModel | dict,
        config: BaseModel | None = None,
    ) -> dict:
        try:
            outputs = []
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
                        tools_dict = self.tools_by_name
                        if callable(tools_dict):
                            tools_dict = tools_dict()  # Call the computed field

                        if isinstance(tools_dict, dict) and tool_name in tools_dict:
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
                    except Exception as e:
                        logger.warning(
                            f"Failed to invoke tool {tool_call.get('name', 'unknown')}: {e}"
                        )
                        continue
            return {"messages": outputs}

        except Exception as e:
            logger.debug(f"Error when calling node {self.name}: {e!s}")
            msg = "Failed during call to a tool Node."
            raise ValueError(msg)
