"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from loguru import logger
from pydantic import BaseModel

from ebiose.core.agent import Agent
from ebiose.core.agent_engine_factory import AgentEngineFactory


# --- Agent Generation Configuration ---
@dataclass
class GenerateAgentConfig:
    """Configuration for agent generation."""

    architect_agent: Agent
    agent_input: BaseModel | dict[str, Any]
    genetic_operator_agent: Agent | None = None
    generated_agent_engine_type: str | None = None
    generated_agent_input: type[BaseModel] | None = None
    generated_agent_output: type[BaseModel] | None = None
    generated_model_endpoint_id: str | None = None
    forge_cycle_id: str | None = None
    forge_description: str | None = None


@dataclass
class CrossoverAgentsConfig:
    """Configuration for agent crossover."""

    crossover_agent: Agent
    input_data: BaseModel
    parent1: Agent
    parent2: Agent | None = None
    generated_agent_engine_type: str | None = None
    generated_agent_input: type[BaseModel] | None = None
    generated_agent_output: type[BaseModel] | None = None
    generated_model_endpoint_id: str | None = None
    forge_cycle_id: str | None = None
    forge_description: str | None = None
    ecosystem: Agent | None = None


# --- Agent Configuration Models ---
class AgentEngineConfig(BaseModel):
    """Configuration for agent engines."""

    engine_type: str
    configuration: dict[str, Any]


class AgentConfig(BaseModel):
    """Complete agent configuration model."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    agent_engine: AgentEngineConfig
    architect_agent: str | None = None
    genetic_operator_agent: str | None = None


if TYPE_CHECKING:
    from ebiose.cloud_client.client import AgentOutputModel


class AgentFactory:
    """Factory for creating and loading agents.

    Provides methods to instantiate agents from configurations,
    API responses, and other sources.
    """

    @staticmethod
    def load_agent_from_api(
        agent_data: AgentOutputModel,
        model_endpoint_id: str | None = None,
    ) -> Agent:
        """Load an agent from API response data.

        Args:
            agent_data: Agent data from API response.
            model_endpoint_id: Optional LLM model endpoint ID.

        Returns:
            Configured Agent instance.

        """
        return AgentFactory.load_agent(
            agent_data.model_dump(by_alias=True),
            model_endpoint_id=model_endpoint_id,
        )

    @staticmethod
    def load_agent(
        agent_config: dict,
        model_endpoint_id: str | None = None,
    ) -> Agent:
        """Load an agent from configuration dictionary.

        Args:
            agent_config: Configuration dictionary with agent settings.
            model_endpoint_id: Optional LLM model endpoint ID.

        Returns:
            Configured Agent instance.

        Raises:
            TypeError: If agent_engine config format is invalid.
            ValueError: If required configuration fields are missing.

        """
        agent_id = agent_config.get("id") or "unknown"

        # Validate agent_engine config structure
        agent_engine_config = agent_config.get("agent_engine", {})
        if not isinstance(agent_engine_config, dict):
            msg = "agent_engine config must be a dict"
            raise TypeError(msg)

        engine_type = agent_engine_config.get("engine_type")
        if engine_type is None:
            msg = "engine_type is required in agent_engine config"
            raise ValueError(msg)

        config_str = agent_engine_config.get("configuration")
        if config_str is None:
            msg = "configuration is required in agent_engine config"
            raise ValueError(msg)

        # creating engine
        configuration = json.loads(config_str)
        agent_engine = AgentEngineFactory.create_engine(
            engine_type=cast("str", engine_type),
            configuration=configuration,
            agent_id=agent_id,
            model_endpoint_id=model_endpoint_id,
        )

        agent_config = agent_config.copy()
        agent_config["agent_engine"] = agent_engine
        agent_config["architect_agent"] = None
        agent_config["genetic_operator_agent"] = None

        return Agent.model_validate(agent_config)

    @staticmethod
    def create_agent_from_api(
        response_dict: AgentOutputModel,
        model_endpoint_id: str | None = None,
    ) -> Agent:
        """Create an Agent instance from API response data.

        Args:
            response_dict: Agent data returned by the cloud API.
            model_endpoint_id: Optional model endpoint override.

        Returns:
            A configured Agent instance.

        Raises:
            ValueError: If required engine configuration is missing or invalid.
            RuntimeError: If engine creation fails.

        """
        # Validate required fields
        if response_dict.agent_engine is None:
            msg = "Agent engine configuration is missing"
            raise ValueError(msg)

        if not response_dict.agent_engine.configuration:
            msg = "Agent engine configuration string is empty"
            raise ValueError(msg)

        if not response_dict.agent_engine.engine_type:
            msg = "Agent engine type is missing"
            raise ValueError(msg)

        # Safe parsing with error handling
        try:
            engine_configuration = json.loads(response_dict.agent_engine.configuration)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in agent engine configuration: {e}"
            raise ValueError(msg) from e

        agent_id = (
            response_dict.uuid or f"agent-{hash(response_dict.name or 'unknown')}"
        )

        # Create engine with validated parameters
        try:
            agent_engine = AgentEngineFactory.create_engine(
                engine_type=response_dict.agent_engine.engine_type,
                configuration=engine_configuration,
                model_endpoint_id=model_endpoint_id,
                agent_id=agent_id,
            )
        except Exception as e:
            msg = f"Failed to create agent engine: {e}"
            raise RuntimeError(msg) from e

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
                architect_agent_id=response_dict.architect_agent_uuid,
                genetic_operator_agent_id=response_dict.genetic_operator_agent_uuid,
                agent_engine=agent_engine,
                parent_ids=response_dict.parent_agent_uuids or [],
            )
        except Exception as e:
            msg = f"Failed to create agent: {e}"
            raise RuntimeError(msg) from e

    @staticmethod
    async def generate_agent(config: GenerateAgentConfig) -> Agent:
        """Generate a new agent using architect agent.

        Args:
            config: Configuration for agent generation

        Returns:
            Generated agent

        """
        architect_agent = config.architect_agent
        agent_input = config.agent_input

        if isinstance(agent_input, dict):
            if (
                architect_agent.agent_engine is None
                or architect_agent.agent_engine.input_model is None
            ):
                msg = "Architect agent input model is not configured"
                raise ValueError(msg)
            agent_input_model = architect_agent.agent_engine.input_model
            agent_input = agent_input_model.model_validate(agent_input)

        output = await architect_agent.run(
            agent_input,
            master_agent_id=architect_agent.id,
            forge_cycle_id=config.forge_cycle_id,
        )

        def _validate_engine_type(engine_type: str | None) -> None:
            if engine_type is None:
                msg = "Generated agent engine type is required"
                raise ValueError(msg)

        try:
            agent_name = config.forge_description
            agent_description = output.description
            agent_engine_configuration = {
                "graph": output.model_dump(),
                "input_model": config.generated_agent_input.model_json_schema()
                if config.generated_agent_input is not None
                else {},
                "output_model": config.generated_agent_output.model_json_schema()
                if config.generated_agent_output is not None
                else {},
            }
            agent_id = "agent-" + str(uuid.uuid4())

            _validate_engine_type(config.generated_agent_engine_type)
            generated_agent_engine = AgentEngineFactory.create_engine(
                cast("str", config.generated_agent_engine_type),
                agent_id=agent_id,
                configuration=agent_engine_configuration,
                model_endpoint_id=config.generated_model_endpoint_id,
            )
        except Exception as e:
            logger.debug(f"Architect agent failed creating a valid agent: {e!s}")
            msg = f"Failed to create agent from architect output: {e}"
            raise RuntimeError(
                msg,
            ) from e

        try:
            new_agent = Agent(
                name=agent_name,
                description=agent_description,
                id=agent_id,
                architect_agent_id=architect_agent.id,
                genetic_operator_agent_id=config.genetic_operator_agent.id
                if config.genetic_operator_agent
                else None,
                agent_engine=generated_agent_engine,
            )
        except Exception as e:
            logger.debug(f"Architect agent failed creating a valid agent: {e!s}")
            msg = f"Failed to generate agent: {e}"
            raise RuntimeError(msg) from e
        return new_agent

    @staticmethod
    async def crossover_agents(config: CrossoverAgentsConfig) -> Agent:
        """Perform crossover between two agents to create offspring.

        Args:
            config: Configuration for crossover operation

        Returns:
            New agent created from crossover

        """
        crossover_agent = config.crossover_agent
        input_data = config.input_data

        output = await crossover_agent.run(
            input_data,
            master_agent_id=config.forge_cycle_id,
            forge_cycle_id=config.forge_cycle_id,
        )

        def _validate_crossover_engine_type(engine_type: str | None) -> None:
            if engine_type is None:
                msg = "Generated agent engine type is required"
                raise ValueError(msg)

        try:
            agent_name = config.forge_description
            agent_description = output.description
            agent_engine_configuration = {
                "graph": output.model_dump(),
                "input_model": config.generated_agent_input.model_json_schema()
                if config.generated_agent_input is not None
                else {},
                "output_model": config.generated_agent_output.model_json_schema()
                if config.generated_agent_output is not None
                else {},
            }
            agent_id = "agent-" + str(uuid.uuid4())

            _validate_crossover_engine_type(config.generated_agent_engine_type)
            generated_agent_engine = AgentEngineFactory.create_engine(
                engine_type=cast("str", config.generated_agent_engine_type),
                agent_id=agent_id,
                configuration=agent_engine_configuration,
                model_endpoint_id=config.generated_model_endpoint_id,
            )

            new_agent = Agent(
                name=agent_name,
                description=agent_description,
                id=agent_id,
                architect_agent_id=config.ecosystem.id if config.ecosystem else None,
                genetic_operator_agent_id=crossover_agent.id,
                agent_engine=generated_agent_engine,
                parent_ids=[config.parent1.id, config.parent2.id]
                if config.parent2
                else [config.parent1.id],
            )
        except Exception as e:
            logger.debug(f"Crossover agent failed creating a valid agent: {e!s}")
            msg = f"Failed to create agent from crossover: {e}"
            raise RuntimeError(msg) from e

        return new_agent
