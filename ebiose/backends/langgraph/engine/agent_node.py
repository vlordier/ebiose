"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from pydantic import BaseModel

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
        state: BaseModel | dict,
        config: BaseModel | None = None,
    ) -> dict:
        _ = config  # Unused parameter
        agent_engine = self.agent.agent_engine
        if agent_engine is None or agent_engine.input_model is None:
            msg = "Agent engine input model is not configured"
            raise RuntimeError(msg)
        state_payload = state.model_dump() if isinstance(state, BaseModel) else state
        agent_input = agent_engine.input_model.model_validate(state_payload)
        response = await self.agent.run(agent_input, master_agent_id=self.agent.id)

        # TODO(xabier): return also a tool message
        if isinstance(response, BaseModel):
            return response.model_dump()
        if isinstance(response, dict):
            return response
        return {"response": response}
