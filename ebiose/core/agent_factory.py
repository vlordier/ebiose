"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

from loguru import logger

from ebiose.cloud_client.client import AgentOutputModel

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ebiose.core.agent import Agent


class AgentFactory:
    @staticmethod
    def load_agent(
        agent_config: dict,
        model_endpoint_id: str | None = None,
    ) -> Agent:
        from ebiose.core.agent import Agent  # Local import
        from ebiose.core.agent_engine_factory import AgentEngineFactory  # Local import

        agent_id = agent_config.get("id") or "unknown"

        # Validate agent_engine config structure
        agent_engine_config = agent_config.get("agent_engine", {})
        if not isinstance(agent_engine_config, dict):
            raise ValueError("agent_engine config must be a dict")

        engine_type = agent_engine_config.get("engine_type")
        if engine_type is None:
            raise ValueError("engine_type is required in agent_engine config")

        config_str = agent_engine_config.get("configuration")
        if config_str is None:
            raise ValueError("configuration is required in agent_engine config")

        # creating engine
        configuration = json.loads(config_str)
        agent_engine = AgentEngineFactory.create_engine(
            engine_type=engine_type,
            configuration=configuration,
            agent_id=agent_id,
            model_endpoint_id=model_endpoint_id,
        )

        agent_config = agent_config.copy()
        agent_config["agent_engine"] = agent_engine
        agent_config["architect_agent"] = None
        agent_config["genetic_operator_agent"] = None
        # agent_config["id"]=agent_engine.agent_id

        return Agent.model_validate(agent_config)

    @staticmethod
    def create_agent_from_api(
        response_dict: AgentOutputModel,
        model_endpoint_id: str | None = None,
    ) -> Agent:
        from ebiose.core.agent import Agent  # Local import
        from ebiose.core.agent_engine_factory import AgentEngineFactory  # Local import

        # Validate required fields
        if response_dict.agentEngine is None:
            raise ValueError("Agent engine configuration is missing")

        if not response_dict.agentEngine.configuration:
            raise ValueError("Agent engine configuration string is empty")

        if not response_dict.agentEngine.engineType:
            raise ValueError("Agent engine type is missing")

        # Safe parsing with error handling
        try:
            engine_configuration = json.loads(response_dict.agentEngine.configuration)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in agent engine configuration: {e}") from e

        agent_id = (
            response_dict.uuid or f"agent-{hash(response_dict.name or 'unknown')}"
        )

        # Create engine with validated parameters
        try:
            agent_engine = AgentEngineFactory.create_engine(
                engine_type=response_dict.agentEngine.engineType,
                configuration=engine_configuration,
                model_endpoint_id=model_endpoint_id,
                agent_id=agent_id,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create agent engine: {e}") from e

        # Determine agent type from name (safe string operations)
        agent_type: Literal["architect", "genetic_operator"] | None = None
        agent_name = response_dict.name or ""

        if "architect" in agent_name:
            agent_type = "architect"
        elif "crossover" in agent_name or "mutation" in agent_name:
            agent_type = "genetic_operator"

        # Create agent with validated data
        try:
            return Agent(
                id=agent_id,
                name=response_dict.name or f"agent-{agent_id}",
                agent_type=agent_type,
                description=response_dict.description,
                architect_agent_id=response_dict.architectAgentUuid,
                genetic_operator_agent_id=response_dict.geneticOperatorAgentUuid,
                agent_engine=agent_engine,
                parent_ids=response_dict.parentAgentUuids or [],
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create agent: {e}") from e

        # TODO(xabier): remove when agent_type is implemented server-side
        agent_type = None
        if response_dict.name and "architect" in response_dict.name:
            agent_type = "architect"
        elif response_dict.name and (
            "crossover" in response_dict.name or "mutation" in response_dict.name
        ):
            agent_type = "genetic_operator"

        return Agent(
            id=agent_id,
            name=response_dict.name or f"agent-{agent_id}",
            agent_type=agent_type,
            description=response_dict.description,
            architect_agent_id=response_dict.architectAgentUuid,
            genetic_operator_agent_id=response_dict.geneticOperatorAgentUuid,
            agent_engine=agent_engine,
            parent_ids=response_dict.parentAgentUuids or [],
        )

    @staticmethod
    async def generate_agent(
        architect_agent: Agent,
        agent_input: dict,
        genetic_operator_agent: Agent | None = None,
        generated_agent_engine_type: str | None = None,
        generated_agent_input: type[BaseModel] | None = None,
        generated_agent_output: type[BaseModel] | None = None,
        generated_model_endpoint_id: str | None = None,
        forge_cycle_id: str | None = None,
        forge_description: str | None = None,
    ) -> Agent:
        from ebiose.core.agent import Agent  # Local import
        from ebiose.core.agent_engine_factory import AgentEngineFactory  # Local import

        output = await architect_agent.run(
            agent_input,
            master_agent_id=architect_agent.id,
            forge_cycle_id=forge_cycle_id,
        )
        try:
            agent_name = forge_description
            agent_description = output.description
            agent_engine_configuration = {
                "graph": output.model_dump(),
                "input_model": generated_agent_input.model_json_schema()
                if generated_agent_input is not None
                else {},
                "output_model": generated_agent_output.model_json_schema()
                if generated_agent_output is not None
                else {},
            }
            agent_id = "agent-" + str(uuid.uuid4())

            generated_agent_engine = AgentEngineFactory.create_engine(
                generated_agent_engine_type,
                agent_id=agent_id,
                configuration=agent_engine_configuration,
                model_endpoint_id=generated_model_endpoint_id,
            )
        except Exception as e:
            logger.debug(f"Architect agent failed creating a valid agent: {e!s}")
            raise RuntimeError(
                f"Failed to create agent from architect output: {e}"
            ) from e

        try:
            new_agent = Agent(
                name=agent_name,
                description=agent_description,
                id=agent_id,
                architect_agent_id=architect_agent.id,
                genetic_operator_agent_id=genetic_operator_agent.id
                if genetic_operator_agent
                else None,
                agent_engine=generated_agent_engine,
            )
        except Exception as e:
            logger.debug(f"Architect agent failed creating a valid agent: {e!s}")
            raise RuntimeError(f"Failed to generate agent: {e}") from e

        return new_agent

    @staticmethod
    async def crossover_agents(
        crossover_agent: Agent,
        input_data: BaseModel,
        generated_agent_engine_type: str | None = None,
        generated_agent_input: type[BaseModel] | None = None,
        generated_agent_output: type[BaseModel] | None = None,
        generated_model_endpoint_id: str | None = None,
        architect_agent: Agent | None = None,
        parent_ids: list[str] | None = None,
        master_agent_id: str | None = None,
        forge_cycle_id: str | None = None,
        forge_description: str | None = None,
    ) -> tuple[Agent, Agent] | Agent:
        from ebiose.core.agent import Agent  # Local import
        from ebiose.core.agent_engine_factory import AgentEngineFactory  # Local import

        output = await crossover_agent.run(
            input_data,
            master_agent_id=master_agent_id,
            forge_cycle_id=forge_cycle_id,
        )
        try:
            agent_name = forge_description
            agent_description = output.description
            agent_engine_configuration = {
                "graph": output.model_dump(),
                "input_model": generated_agent_input.model_json_schema()
                if generated_agent_input is not None
                else {},
                "output_model": generated_agent_output.model_json_schema()
                if generated_agent_output is not None
                else {},
            }
            agent_id = "agent-" + str(uuid.uuid4())
            generated_agent_engine = AgentEngineFactory.create_engine(
                engine_type=generated_agent_engine_type,
                agent_id=agent_id,
                configuration=agent_engine_configuration,
                model_endpoint_id=generated_model_endpoint_id,
            )

            new_agent = Agent(
                name=agent_name,
                description=agent_description,
                id=agent_id,
                architect_agent_id=architect_agent.id if architect_agent else None,
                genetic_operator_agent_id=crossover_agent.id,
                agent_engine=generated_agent_engine,
                parent_ids=parent_ids,
            )
        except Exception as e:
            logger.debug(f"Crossover agent failed creating a valid agent: {e!s}")
            new_agent = None

        return new_agent
