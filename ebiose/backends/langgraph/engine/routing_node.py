"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Literal

from langchain_core.messages import AIMessage, AnyMessage, ToolCall, ToolMessage

from ebiose.backends.langgraph.engine.states import (
    LangGraphEngineInputState,
    LangGraphEngineOutputState,
)
from ebiose.core.engines.graph_engine.nodes.routing_node import (
    RoutingNode,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydantic import BaseModel


class InputState(LangGraphEngineInputState):
    """Input state for LangGraph routing nodes."""

    last_message: AnyMessage
    possible_output: Sequence[str]


class OutputState(LangGraphEngineOutputState):
    """Output state for LangGraph routing nodes."""

    output_condition: str | None = None
    condition: Literal["found", "not_found"] | None = None


class LangGraphRoutingNode(RoutingNode):
    """LangGraph routing node that selects a path based on message content."""

    input_state_model: type[BaseModel] = InputState
    output_state_model: type[BaseModel] = OutputState

    def get_messages(
        self,
        condition: str,
        error_message: str | None = None,
    ) -> list[AnyMessage]:
        """Create routing tool messages based on selection outcome.

        Args:
            condition: Routing condition ("found" or error state).
            error_message: Optional error context when routing fails.

        Returns:
            A list of LangChain messages describing routing outcome.

        """
        tool_call_id = f"call_{self.id}_{uuid.uuid4()}"[40]
        tool_call = ToolCall(
            name=self.name,
            args={},
            id=tool_call_id,
        )

        messages: list[AnyMessage] = [
            AIMessage(
                content="",
                tool_calls=[tool_call],
            ),
        ]

        if condition == "found":
            messages.append(
                ToolMessage(
                    name=self.name,
                    content="Regex routing successful",
                    tool_call_id=tool_call_id,
                ),
            )
        else:
            messages.append(
                ToolMessage(
                    name=self.name,
                    content=f"Regex routing failed with error:\n{error_message}",
                    tool_call_id=tool_call_id,
                ),
            )

        return messages

    async def call_node(
        self,
        state: BaseModel | dict,
        config: BaseModel | None = None,
    ) -> dict:
        """Route execution based on the last message content.

        Args:
            state: Input state containing messages and possible outputs.
            config: Optional runtime configuration (unused).

        Returns:
            Output payload with selected routing condition and messages.

        """
        _ = config  # Unused parameter
        # Handle union type: state can be InputState or dict
        if isinstance(state, dict):
            messages = state.get("messages", [])
            last_message = state.get("last_message")
            possible_output = state.get("possible_output", [])

            if len(messages) == 0 and last_message:
                # Use last_message if available
                content = (
                    last_message.get("content", "")
                    if isinstance(last_message, dict)
                    else str(last_message)
                )
                last_message_str = str(content).lower()
            elif len(messages) > 0:
                # Use last message from messages array
                last_msg = messages[-1]
                content = (
                    last_msg.get("content", "")
                    if isinstance(last_msg, dict)
                    else str(last_msg)
                )
                last_message_str = str(content).lower()
            elif len(messages) > 0:
                # Use last message from messages array
                last_msg = messages[-1]
                content = (
                    last_msg.get("content", "")
                    if isinstance(last_msg, dict)
                    else str(last_msg)
                )
                last_message_str = content.lower()
            else:
                last_message_str = ""
        else:
            # state is BaseModel - use getattr for safety
            messages = getattr(state, "messages", [])
            last_message = getattr(state, "last_message", None)
            possible_output = getattr(state, "possible_output", [])

            if len(messages) == 0 and last_message:
                content = str(getattr(last_message, "content", ""))
            elif len(messages) > 0:
                last_msg = messages[-1]
                content = str(getattr(last_msg, "content", ""))
            else:
                content = ""
            last_message_str = content.lower()

        output_condition = None
        count = 0
        for condition in possible_output:
            if isinstance(condition, str) and condition.lower() in last_message_str:
                count += 1
                output_condition = condition

        if count == 1:
            return self.output_state_model(
                messages=self.get_messages(condition="found")
                if hasattr(self, "output_state_model")
                else [],
                condition="found",
                output_condition=output_condition,
            ).model_dump()
        error_message = (
            "The message does not contain any of the possible conditions."
            if count == 0
            else "The message contains more than one of the possible conditions."
        )
        return self.output_state_model(
            messages=self.get_messages("error", error_message)
            if hasattr(self, "output_state_model")
            else [],
            error_message=error_message,
            condition="not_found",
            output_condition=output_condition,
        ).model_dump()
