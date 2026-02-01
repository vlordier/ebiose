"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from loguru import logger

from ebiose.core.agent_factory import (
    AgentFactory,
    CrossoverAgentsConfig,
    GenerateAgentConfig,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ebiose.core.agent import Agent
    from ebiose.core.agent_forge import AgentForge

T = TypeVar("T")


@dataclass
class CrossoverAgentTaskConfig:
    """Configuration for crossover agent task."""

    forge: AgentForge
    genetic_operator_agent: Agent
    crossover_agent_input: BaseModel
    architect_agent: Agent | None
    parent1: Agent
    parent2: Agent | None
    master_agent_id: str | None = None
    forge_cycle_id: str | None = None


# init in ecosystem
async def architect_agent_task(
    forge: AgentForge,
    architect_agent: Agent,
    architect_agent_input: BaseModel,
    genetic_operator_agent: Agent | None,
    forge_cycle_id: str | None = None,
) -> Agent | None:
    if genetic_operator_agent is None:
        return None

    response = None
    try:
        gen_config = GenerateAgentConfig(
            architect_agent=architect_agent,
            agent_input=architect_agent_input,
            genetic_operator_agent=genetic_operator_agent,
            generated_agent_engine_type=forge.default_generated_agent_engine_type,
            generated_model_endpoint_id=forge.default_model_endpoint_id,
            generated_agent_input=forge.agent_input_model,
            generated_agent_output=forge.agent_output_model,
            forge_cycle_id=forge_cycle_id,
            forge_description=forge.description,
        )
        response = await AgentFactory.generate_agent(gen_config)
    except (ValueError, TypeError, RuntimeError):
        logger.debug(
            f"Architect agent {architect_agent.id} failed creating a valid agent for {forge.name}. Retrying once.",
        )
        gen_config = GenerateAgentConfig(
            architect_agent=architect_agent,
            agent_input=architect_agent_input,
            genetic_operator_agent=genetic_operator_agent,
            generated_agent_engine_type=forge.default_generated_agent_engine_type,
            generated_model_endpoint_id=forge.default_model_endpoint_id,
            generated_agent_input=forge.agent_input_model,
            generated_agent_output=forge.agent_output_model,
            forge_cycle_id=forge_cycle_id,
            forge_description=forge.description,
        )
        response = await AgentFactory.generate_agent(gen_config)
    return response


# crossover and mutate
async def crossover_agent_task(
    config: CrossoverAgentTaskConfig,
) -> Agent | None:
    forge = config.forge
    genetic_operator_agent = config.genetic_operator_agent
    crossover_agent_input = config.crossover_agent_input
    architect_agent = config.architect_agent
    parent1 = config.parent1
    parent2 = config.parent2
    forge_cycle_id = config.forge_cycle_id

    result = None
    try:
        crossover_config = CrossoverAgentsConfig(
            crossover_agent=genetic_operator_agent,
            input_data=crossover_agent_input,
            parent1=parent1,
            parent2=parent2,
            generated_agent_engine_type=forge.default_generated_agent_engine_type,
            generated_model_endpoint_id=forge.default_model_endpoint_id,
            generated_agent_input=forge.agent_input_model,
            generated_agent_output=forge.agent_output_model,
            forge_cycle_id=forge_cycle_id,
            forge_description=forge.description,
            ecosystem=architect_agent,
        )
        result = await AgentFactory.crossover_agents(crossover_config)
    except (ValueError, TypeError, RuntimeError):
        parent2_id = parent2.id if parent2 is not None else "None"
        logger.debug(
            f"Error while generating offspring from {[parent1.id, parent2_id]}. Falling back to architect agent.",
        )
        if architect_agent is None:
            return None
        if architect_agent.agent_engine is None or architect_agent.agent_engine.input_model is None:
            return None
        fallback_input = architect_agent.agent_engine.input_model(
            forge_description=forge.description,
        )
        gen_config = GenerateAgentConfig(
            architect_agent=architect_agent,
            agent_input=fallback_input,
            genetic_operator_agent=genetic_operator_agent,
            generated_agent_engine_type=forge.default_generated_agent_engine_type,
            generated_model_endpoint_id=forge.default_model_endpoint_id,
            generated_agent_input=forge.agent_input_model,
            generated_agent_output=forge.agent_output_model,
            forge_cycle_id=forge_cycle_id,
            forge_description=forge.description,
        )
        result = await AgentFactory.generate_agent(gen_config)

    return result
