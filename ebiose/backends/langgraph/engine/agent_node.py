"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

from ebiose.core.engines.graph_engine.nodes.agent_node import AgentNode


class InputState(BaseModel):
    pass


class OutputState(BaseModel):
    pass


class LangGraphAgentNode(AgentNode):
    input_state_model: type[BaseModel] = InputState
    output_state_model: type[BaseModel] = OutputState

    async def call_node(
        self,
        agent_state: InputState,
        config: "Runtime[BaseModel]" | None = None,
    ) -> dict:  # type: ignore  # noqa: PGH003
        agent_input = self.agent.agent_engine.input_model.model_validate(
            agent_state.model_dump(),
        )
        response = await self.agent.run(agent_input)

        # TODO(xabier): return also a tool message
        return response.model_dump()
