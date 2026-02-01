"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import traceback
from typing import Any, cast

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from ebiose.backends.langgraph.engine.states import (
    LangGraphEngineInputState,
    LangGraphEngineOutputState,
)
from ebiose.backends.langgraph.llm_api import LangGraphLLMApi, LLMCallConfig
from ebiose.core.engines.graph_engine.nodes import (
    get_n_llm_nodes_constraint_string,
    get_node_types_docstrings,
)
from ebiose.core.engines.graph_engine.nodes.llm_node import LLMNode
from ebiose.core.engines.graph_engine.utils import get_placeholders


class InputState(LangGraphEngineInputState):
    pass


class OutputState(LangGraphEngineOutputState):
    pass


class LangGraphLLMNodeError(Exception):
    """Custom exception for errors during LLM calls."""

    def __init__(
        self,
        message: str,
        original_exception: Exception | None = None,
        llm_identifier: str | None = None,
    ) -> None:
        super().__init__(message)
        self.original_exception = original_exception
        self.llm_identifier = llm_identifier

    def __str__(self) -> str:
        error_msg = "LangGraphLLMNodeError"
        if self.llm_identifier:
            error_msg += f" (LLM: {self.llm_identifier})"
        error_msg += f": {super().__str__()}"
        if self.original_exception:
            orig_traceback = traceback.format_exception(
                type(self.original_exception),
                self.original_exception,
                self.original_exception.__traceback__,
            )
            error_msg += f"\n--- Caused by ---\n{''.join(orig_traceback)}"
        return error_msg


class LangGraphLLMNode(LLMNode):
    temperature: float | None = None
    tools: list | None = Field(default_factory=list)
    input_state_model: type[BaseModel] = InputState
    output_state_model: type[BaseModel] = OutputState

    def _validate_and_extract_runtime(self, state: BaseModel | dict, config: BaseModel | None) -> Runtime:
        """Validate state and config, return Runtime."""
        if not isinstance(state, InputState):
            msg = "Invalid state type for LangGraphLLMNode"
            raise TypeError(msg)

        if config is None or not isinstance(config, Runtime):
            msg = "Runtime configuration is required for LangGraphLLMNode"
            raise TypeError(msg)

        if config.context is None:
            msg = "Runtime context is missing"
            raise ValueError(msg)

        return config

    def _build_system_message(self, runtime: Runtime, input_data: BaseModel) -> str:
        """Build system message with context prompt."""
        shared_context_prompt = runtime.context.shared_context_prompt
        placeholders = get_placeholders(shared_context_prompt)

        # TODO(xabier): this is a temporary solution to generate missing fields for achitect agents
        # We cast to Any because these fields are dynamically checked and set based on placeholders
        dynamic_input = cast("Any", input_data)
        if "node_types_description" in placeholders:
            dynamic_input.node_types_description = get_node_types_docstrings(
                dynamic_input.node_types,
            )
        if "n_llm_nodes_constraint_string" in placeholders:
            dynamic_input.n_llm_nodes_constraint_string = (
                get_n_llm_nodes_constraint_string(
                    random_n_llm_nodes=dynamic_input.random_n_llm_nodes,
                    max_llm_nodes=dynamic_input.max_llm_nodes,
                )
            )
        if len(placeholders) > 0:
            shared_context_prompt = shared_context_prompt.format(
                **input_data.model_dump(),
            )
        else:
            shared_context_prompt += "\nInput: " + input_data.model_dump_json()

        return shared_context_prompt + f"\nYour are the {self.name} node."

    def _build_human_message(self, state: InputState, runtime: Runtime, input_data: BaseModel, output_conditions: list[str]) -> str:
        """Build human message with user request."""
        if len(state.error_message) == 0:
            human_prompt = self.prompt.format(
                output_schema=runtime.context.output_model.schema_json(indent=2),
                **input_data.model_dump(),
            )
        else:
            # TODO(issue): improve the error message
            human_prompt = f"Your last response triggered the following error:\n{state.error_message}\nFix it."

        if len(output_conditions) > 0:
            human_prompt += f"\nAccording to your response, append at the end of your response one of the following conditions: {output_conditions}"

        return human_prompt

    async def call_node(
        self,
        state: BaseModel | dict,
        config: BaseModel | None = None,
    ) -> dict:
        runtime = self._validate_and_extract_runtime(state, config)
        state = cast("InputState", state)

        try:
            model_endpoint_id = runtime.context.model_endpoint_id
            agent_id = runtime.context.agent_id

            output_conditions = []
            if hasattr(runtime.context, self.id):
                node_context = getattr(runtime.context, self.id)
                if "output_conditions" in node_context:
                    output_conditions = node_context["output_conditions"]

            input_data = cast("Any", state.input)
            system_msg = self._build_system_message(runtime, input_data)
            human_msg = self._build_human_message(state, runtime, input_data, output_conditions)

            prompts: list[AnyMessage] = [SystemMessage(system_msg)]
            prompts += state.messages
            prompts.append(HumanMessage(human_msg))

            # instantiate model
            call_config = LLMCallConfig(
                model_endpoint_id=model_endpoint_id,
                messages=prompts,
                agent_id=agent_id,
                temperature=self.temperature or 0.7,
                tools=self.tools or [],
            )
            response = await LangGraphLLMApi.process_llm_call(call_config)
            messages: list[AnyMessage] = [response]
            if self.tools and len(self.tools) > 0:
                tool_calls = getattr(response, "tool_calls", []) or []
                new_tool_messages = [
                    ToolMessage(
                        content=str(tool),
                        tool_call_id=str(tool.get("id")),
                    )
                    for tool in tool_calls
                ]
                messages.extend(new_tool_messages)
            return OutputState(messages=messages).model_dump()

        except Exception as e:
            logger.debug(f"Error when calling node {self.name}: {e!s}")
            msg = "Failed during call to an LLM Node."
            raise LangGraphLLMNodeError(msg, e, f"{self.name}({self.id})") from e
