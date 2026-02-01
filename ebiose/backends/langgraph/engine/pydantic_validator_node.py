"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import ast
import uuid
from typing import Literal

from langchain_core.messages import AIMessage, AnyMessage, ToolCall, ToolMessage
from pydantic import BaseModel, Field

from ebiose.backends.langgraph.engine.states import (
    LangGraphEngineInputState,
    LangGraphEngineOutputState,
)
from ebiose.core.engines.graph_engine.nodes.pydantic_validator_node import (
    PydanticValidatorNode,
)


class InputState(LangGraphEngineInputState):
    output_model: type[BaseModel] | None = Field(None, exclude=True)


class OutputState(LangGraphEngineOutputState):
    condition: Literal["success", "failure"] | None = None


class LangGraphPydanticValidatorNode(PydanticValidatorNode):
    input_state_model: type[BaseModel] = InputState
    output_state_model: type[BaseModel] = OutputState

    def get_messages(
        self,
        condition: str,
        error: Exception | None = None,
    ) -> list[AnyMessage]:
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

        if condition == "success":
            messages.append(
                ToolMessage(
                    name=self.name,
                    content="Pydantic validation successful",
                    tool_call_id=tool_call_id,
                ),
            )
        else:
            messages.append(
                ToolMessage(
                    name=self.name,
                    content=f"Pydantic validation failed with error:\n{error!s}",
                    tool_call_id=tool_call_id,
                ),
            )

        return messages

    async def call_node(
        self,
        state: BaseModel | dict,
        config: BaseModel | None = None,
    ) -> dict:
        try:
            # Handle union type: state can be BaseModel or dict
            messages = (
                state.get("messages", [])
                if isinstance(state, dict)
                else getattr(state, "messages", [])
            )

            tool_messages = []
            for message in reversed(messages):
                if isinstance(message, ToolMessage):
                    tool_messages.append(message)
                else:
                    break

            output_model = getattr(config, "output_model", None) if config else None
            tool_contents = [
                ast.literal_eval(str(tool_message.content))
                for tool_message in tool_messages
            ]
            tool_content_args = {}
            for tool_content in tool_contents:
                tool_content_args.update(tool_content["args"])

            # Validate before entering try block
            if output_model is None or not hasattr(output_model, "model_validate"):
                msg = "Output model not properly configured"
                return {
                    "messages": self.get_messages("failure", error=ValueError(msg)),
                    "output": None,
                    "error_message": msg,
                    "condition": "failure",
                }

            try:
                output = output_model.model_validate(tool_content_args)
            except (ValueError, TypeError, AttributeError) as e:
                return {
                    "messages": self.get_messages("failure", error=e),
                    "output": None,
                    "error_message": str(e),
                    "condition": "failure",
                }

            return {
                "messages": self.get_messages("success"),
                "output": output,
                "condition": "success",
            }

        except (ValueError, TypeError, AttributeError, KeyError) as e:
            # TODO(xabier): send a different condition (eg validation_error vs other_error)
            return {
                "messages": self.get_messages("failure", error=e),
                "output": None,
                "error_message": str(e),
                "condition": "failure",
            }
