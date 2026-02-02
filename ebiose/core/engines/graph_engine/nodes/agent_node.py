"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from ebiose.core.engines.graph_engine.nodes.node import BaseNode

if TYPE_CHECKING:
    import builtins

    from ebiose.core.agent import Agent


class AgentNode(BaseNode, abc.ABC):
    """Base node that delegates execution to an Agent instance."""

    type: Literal["AgentNode"] = "AgentNode"
    name: str = Field(default_factory=lambda: "agent_node")
    # TODO(xabier): agent_id instead of agent, as agent embeds the agent_engine for now
    # and an architect agent will select an agent without considering the type of agent engine
    agent: Agent = Field(..., description="The agent to be used")

    def get_input_model(self) -> builtins.type[BaseModel] | None:
        """Return the input model from the agent engine, if available."""
        if self.agent.agent_engine is None:
            return None
        return self.agent.agent_engine.input_model

    def get_output_model(self) -> builtins.type[BaseModel] | None:
        """Return the output model from the agent engine, if available."""
        if self.agent.agent_engine is None:
            return None
        return self.agent.agent_engine.output_model
