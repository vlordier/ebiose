"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field
from sortedcontainers import SortedList

from ebiose.core.engines.graph_engine.utils import GraphUtils
from ebiose.core.model_endpoint import ModelEndpoints
from ebiose.tools.embedding_helper import embedding_distance

if TYPE_CHECKING:
    from ebiose.core.agent import Agent
    from ebiose.core.agent_forge import AgentForge


class Ecosystem(BaseModel):
    """Collection of agents evolving together in a shared ecosystem."""

    id: str = Field(default_factory=lambda: f"forge-cycle-{uuid4()!s}")
    initial_architect_agents: list[Agent] | None = None
    initial_genetic_operator_agents: list[Agent] | None = None
    agents: dict[str, Agent] = Field(default_factory=dict)
    forge_list: ClassVar[list[AgentForge]] = []
    agent_forge_distances: ClassVar[dict[str, SortedList]] = {}
    model_endpoint_ids: ClassVar[list[str]] = []

    @classmethod
    def new(cls, initial_agents: list[Agent] | None = None) -> Ecosystem:
        """Create a new ecosystem with initial architect and genetic operator agents.

        Args:
            initial_agents: Optional list of initial agents to add to the ecosystem.

        Returns:
            A new Ecosystem instance.

        """
        initial_architect_agents = [
            GraphUtils.get_architect_agent(
                ModelEndpoints.get_default_meta_agent_endpoint_id(),
            ),
        ]
        initial_genetic_operator_agents = [
            GraphUtils.get_crossover_agent(
                ModelEndpoints.get_default_meta_agent_endpoint_id(),
            ),
            GraphUtils.get_mutation_agent(
                ModelEndpoints.get_default_meta_agent_endpoint_id(),
            ),
        ]
        # TODO(xabier): fix this import to avoid circular dependency

        cls.model_rebuild()
        agents_dict = {agent.id: agent for agent in (initial_agents or [])}
        return cls(
            initial_architect_agents=initial_architect_agents,
            initial_genetic_operator_agents=initial_genetic_operator_agents,
            agents=agents_dict,
        )

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent from the ecosystem by ID.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            The Agent if found, None otherwise.

        """
        for agent in self.agents.values():
            if agent.id == agent_id:
                return agent
        return None

    async def select_agents_for_forge(
        self,
        forge: AgentForge,
        n_agents: int,
    ) -> list[Agent]:
        """Select agents from the ecosystem for a given forge.

        Args:
            forge: Target forge selecting agents.
            n_agents: Number of agents to select.

        Returns:
            List of selected agents.

        """
        self.add_forge(forge)
        if n_agents <= 0:
            return []
        selected_agents = []
        agent_forge_distances = self.agent_forge_distances[forge.id]
        for _ in range(n_agents):
            if len(agent_forge_distances) == 0:
                break
            agent, _ = agent_forge_distances.pop(0)
            selected_agents.append(agent)
        return selected_agents

    def add_forge(self, forge: AgentForge) -> None:
        """Add a forge to the ecosystem and compute agent-forge distances.

        Args:
            forge: The AgentForge to add to the ecosystem.

        """
        self.forge_list.append(forge)
        # Initialize SortedList with existing agents and their distances
        self.agent_forge_distances[forge.id] = SortedList(
            [
                (
                    agent,
                    embedding_distance(
                        agent.description_embedding or [],
                        forge.description_embedding or [],
                    ),
                )
                for agent in self.agents.values()
            ],
            key=lambda x: x[1],
        )

    def _add_new_born_agent(self, new_agent: Agent) -> None:
        """Add a newly created agent to the ecosystem and update distances.

        Args:
            new_agent: The new agent to add to the ecosystem.

        """
        for forge in self.forge_list:
            distance = embedding_distance(
                new_agent.description_embedding or [],
                forge.description_embedding or [],
            )
            self.agent_forge_distances[forge.id].add((new_agent, distance))

        self.agents[new_agent.id] = new_agent
