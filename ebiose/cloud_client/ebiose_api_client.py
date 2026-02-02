"""High-level Ebiose cloud API client helpers."""

import functools
import json
import random
import re
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

from loguru import logger
from pydantic import BaseModel, Field

from ebiose.cloud_client.client import (
    AgentEngineInputModel,
    AgentInputModel,
    AgentType,
    EbioseCloudClient,
    EbioseCloudError,
    ForgeCycleInputModel,
    ForgeInputModel,
    LogEntryInputModel,
)
from ebiose.core.agent import Agent
from ebiose.core.agent_engine_factory import AgentEngineFactory
from ebiose.core.agent_factory import AgentFactory
from ebiose.core.ecosystem import Ecosystem
from ebiose.core.engines.graph_engine.edge import Edge
from ebiose.core.engines.graph_engine.graph import Graph
from ebiose.core.engines.graph_engine.nodes import EndNode, LLMNode, StartNode
from ebiose.core.engines.graph_engine.utils import GraphUtils
from ebiose.core.model_endpoint import ModelEndpoints

if TYPE_CHECKING:
    from ebiose.core.forge_cycle import CloudForgeCycleConfig

R = TypeVar("R")  # For generic return types


ES_INDEX = "test-pva4"


def build_agent_input_model(
    agent: "Agent",
    forge_cycle_id: str | None,
) -> AgentInputModel:
    """Format the agent for the API."""
    if agent.agent_engine is None:
        msg = f"Agent {agent.id} has no engine"
        raise ValueError(msg)

    agent_engine = AgentEngineInputModel(
        engine_type=agent.agent_engine.engine_type,
        configuration=agent.agent_engine.serialize_configuration(),
    )
    # TODO(xabier): make this more straightforward
    if agent.agent_type == "architect":
        agent_type = AgentType(2)
    elif agent.agent_type == "genetic_operator":
        agent_type = AgentType(1)
    else:
        agent_type = AgentType(0)

    return AgentInputModel(
        name=agent.name,
        description=agent.description,
        architect_agent_uuid=agent.architect_agent_id,
        genetic_operator_agent_uuid=agent.genetic_operator_agent_id,
        agent_engine=agent_engine,
        description_embedding=agent.description_embedding,
        agent_type=agent_type,
        parent_agent_uuids=agent.parent_ids,
        origin_forge_cycle_uuid=forge_cycle_id,
    )


class EbioseAPIClient:
    """Facade client for interacting with Ebiose cloud services."""

    _client: EbioseCloudClient | None = None

    @classmethod
    def _get_client(cls) -> EbioseCloudClient:
        """Get the API client, initializing it if necessary."""
        if cls._client is None:
            base_url = ModelEndpoints.get_ebiose_api_base()
            if base_url is None:
                msg = "Ebiose API base URL is not configured"
                raise ValueError(msg)
            cls._client = EbioseCloudClient(
                base_url=base_url,
                api_key=ModelEndpoints.get_ebiose_api_key(),
            )
        return cls._client

    @classmethod
    def set_client(cls) -> None:
        """Set the API client with the provided API key."""
        cls._get_client()  # Initialize the client

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert a PascalCase or camelCase string to snake_case."""
        # Example: "EcosystemUuid" -> "ecosystem_uuid"
        # Example: "Region" -> "region"
        # This regex finds a lowercase letter or digit followed by an uppercase letter
        # and inserts an underscore between them.
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        # This handles cases like "UUID" -> "_UUID", then we handle the rest.
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()

    @classmethod
    def _convert_data_keys(cls, data: Any) -> Any:  # noqa: ANN401
        """Recursively traverse a data structure and convert keys.

        Converts all dictionary keys from PascalCase to snake_case.
        """
        if isinstance(data, list):
            # If it's a list, apply the conversion to each item in the list.
            return [cls._convert_data_keys(item) for item in data]

        if isinstance(data, dict):
            # If it's a dictionary, create a new dict with converted keys.
            # Recursively call the function on values to handle nested structures.
            return {
                cls._to_snake_case(key): cls._convert_data_keys(value)
                for key, value in data.items()
            }

        # If it's not a list or dict, return the data as is.
        return data

    # This is the updated decorator within YourClass
    @staticmethod
    def _handle_api_errors(func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap function to handle client initialization and API errors.

        Also converts response keys from PascalCase to snake_case.
        """

        @functools.wraps(func)
        def wrapper(
            cls: type["EbioseAPIClient"],
            *args: Any,  # noqa: ANN401
            **kwargs: Any,  # noqa: ANN401
        ) -> Any:  # noqa: ANN401
            try:
                if cls._client is None:
                    cls.set_client()

                # 1. Call the original method to get the raw API response
                pascal_case_result = func(cls, *args, **kwargs)

            except EbioseCloudError as e:
                logger.debug(f"An API error occurred: {e}")
                if e.response_text:
                    logger.debug(f"Raw error response from server: {e.response_text}")
                return None

            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.debug(f"An unexpected error occurred: {e}")
                return None
            else:
                # 2. If the call was successful, convert the keys before returning
                if pascal_case_result is not None:
                    return cls._convert_data_keys(pascal_case_result)

                # Return None if the original result was None
                return None

        return cast("Callable[..., Any]", wrapper)

    @classmethod
    @_handle_api_errors
    def get_user_id(cls) -> str | None:
        """Get the user ID from the API."""
        response = cls._get_client().user_info()
        return response.uuid

    @classmethod
    @_handle_api_errors
    def log(cls, message: dict[str, Any]) -> None:
        """Log a message to the API."""
        json_message = json.dumps(message, sort_keys=True)
        log_entry = LogEntryInputModel(
            index=ES_INDEX,
            data=json_message,
        )
        cls._get_client().add_log_entry(data=log_entry)

    @classmethod
    @_handle_api_errors
    def get_ecosystems(cls) -> list | None:
        """Get all ecosystem UUIDs."""
        list_of_ecosystems = cls._get_client().list_ecosystems()

        if list_of_ecosystems:
            return list_of_ecosystems
        logger.debug("No ecosystems were found.")
        return []

    @classmethod
    @_handle_api_errors
    def get_first_ecosystem_uuid(cls) -> str | None:
        """Get the first ecosystem UUID."""
        ecosystems = cls.get_ecosystems()
        return ecosystems[0].uuid if ecosystems else None

    @classmethod
    @_handle_api_errors
    def delete_agents(cls, ecosystem_id: str, agent_ids: list[str]) -> None:
        """Delete agents in an ecosystem."""
        if not agent_ids:
            logger.debug("No agents to delete.")
            return

        logger.debug(
            f"Deleting agents with IDs: {agent_ids} from ecosystem {ecosystem_id}",
        )
        cls._get_client().delete_agents_from_ecosystem(
            ecosystem_uuid=ecosystem_id,
            agent_uuids=agent_ids,
        )

    @classmethod
    @_handle_api_errors
    def add_agents_to_ecosystem(
        cls,
        agents: list["Agent"],
        ecosystem_id: str,
    ) -> None:
        """Post agents in an ecosystem."""
        agents_data = [
            build_agent_input_model(agent, forge_cycle_id=None) for agent in agents
        ]
        cls._get_client().add_agents_to_ecosystem(
            ecosystem_uuid=ecosystem_id,
            agents_data=agents_data,
        )

    @classmethod
    @_handle_api_errors
    def add_agents_from_forge_cycle(
        cls,
        forge_cycle_id: str,
        agents: list["Agent"],
    ) -> None:
        """Post agents in a forge cycle."""
        agents_data = [
            build_agent_input_model(agent, forge_cycle_id=forge_cycle_id)
            for agent in agents
        ]
        cls._get_client().add_agents_during_forge_cycle(
            forge_cycle_uuid=forge_cycle_id,
            agents_data=agents_data,
        )

    @classmethod
    @_handle_api_errors
    def add_agent_from_forge_cycle(
        cls,
        forge_cycle_id: str,
        agent: "Agent",
    ) -> str:
        """Post a single agent in a forge cycle."""
        agent_data = build_agent_input_model(agent, forge_cycle_id=forge_cycle_id)
        agent_output_model = cls._get_client().add_agent_during_forge_cycle(
            forge_cycle_uuid=forge_cycle_id,
            data=agent_data,
        )

        if agent_output_model.uuid is None:
            msg = "Agent UUID missing in forge cycle response"
            raise ValueError(msg)
        return agent_output_model.uuid

    @classmethod
    @_handle_api_errors
    def get_ecosystem(cls, ecosystem_id: str) -> Ecosystem | None:
        """Get an ecosystem by its UUID."""
        # TODO(xabier): we don't need the ecosystem to be loaded from the API,
        # we just need to get architect and genetic operator agents from the API
        # based on the selected agents from the ecosystem.
        response = cls._get_client().get_ecosystem(uuid=ecosystem_id)
        agents = [
            AgentFactory.load_agent_from_api(agent_data)
            for agent_data in response.agents or []
        ]
        Ecosystem.model_rebuild()
        if response.uuid is None:
            msg = "Ecosystem UUID missing in response"
            raise ValueError(msg)
        return Ecosystem(
            id=response.uuid,
            agents={agent.id: agent for agent in agents},
        )

    @classmethod
    @_handle_api_errors
    def get_agents(
        cls,
        ecosystem_id: str,
        *,
        return_ids_only: bool,
    ) -> list[str] | list["Agent"] | None:
        """Retrieve agents from an ecosystem.

        Args:
            ecosystem_id: UUID of the ecosystem to query.
            return_ids_only: If True, return only agent UUIDs.

        Returns:
            List of agent IDs or Agent instances, or None on failure.

        """
        response = cls._get_client().list_agents_in_ecosystem(
            ecosystem_uuid=ecosystem_id,
        )
        if return_ids_only:
            return [r.uuid for r in response if r.uuid is not None]

        agents = []
        for r in response:
            try:
                agent = AgentFactory.load_agent_from_api(r)
                agents.append(agent)
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.debug(f"Failed to load agent from API: {e}")
        return agents

    @classmethod
    @_handle_api_errors
    def add_forge(
        cls,
        name: str,
        description: str,
        ecosystem_id: str,
    ) -> str | None:
        """Create a forge for an ecosystem.

        Args:
            name: Forge name.
            description: Forge description.
            ecosystem_id: Ecosystem UUID.

        Returns:
            The created forge UUID if available.

        """
        forge_input_model = ForgeInputModel(
            name=name,
            description=description,
            ecosystem_uuid=ecosystem_id,
        )
        response = cls._get_client().add_forge(
            data=forge_input_model,
        )
        return response.uuid

    @classmethod
    @_handle_api_errors
    def start_new_forge_cycle(
        cls,
        ecosystem_id: str,
        forge_name: str,
        forge_description: str,
        forge_cycle_config: "CloudForgeCycleConfig",
        *,
        override_key: bool | None = None,
    ) -> tuple[str, str, str, str]:
        """Start a new forge cycle and return credentials and identifiers.

        Args:
            ecosystem_id: Ecosystem UUID.
            forge_name: Forge name to create.
            forge_description: Forge description.
            forge_cycle_config: Forge cycle configuration.
            override_key: Whether to override budget key.

        Returns:
            Tuple of (lite_llm_key, base_url, forge_cycle_uuid, forge_uuid).

        """
        forge_id = cls.add_forge(
            name=forge_name,
            description=forge_description,
            ecosystem_id=ecosystem_id,
        )

        forge_cycle_input = ForgeCycleInputModel(
            n_agents_in_population=forge_cycle_config.n_agents_in_population,
            n_selected_agents_from_ecosystem=forge_cycle_config.n_selected_agents_from_ecosystem,
            n_best_agents_to_return=forge_cycle_config.n_best_agents_to_return,
            replacement_ratio=forge_cycle_config.replacement_ratio,
            tournament_size_ratio=forge_cycle_config.tournament_size_ratio,
            local_results_path=None,  # forge_cycle_config.local_results_path, no use to send it to the server side
            budget=forge_cycle_config.budget,
        )

        new_cycle_output = cls._get_client().start_new_forge_cycle(
            forge_uuid=forge_id,
            data=forge_cycle_input,
            override_key=override_key,
        )

        if (
            new_cycle_output.lite_llm_key is None
            or new_cycle_output.base_url is None
            or new_cycle_output.forge_cycle_uuid is None
        ):
            msg = "Forge cycle response missing required fields"
            raise ValueError(msg)

        return (
            new_cycle_output.lite_llm_key,
            new_cycle_output.base_url,
            new_cycle_output.forge_cycle_uuid,
            forge_id,
        )

    @classmethod
    @_handle_api_errors
    def select_agents(cls, nb_agents: int, forge_cycle_uuid: str) -> list["Agent"]:
        """Select agents from an ecosystem."""
        response = cls._get_client().select_agents_for_forge_cycle(
            forge_cycle_uuid=forge_cycle_uuid,
            nb_agents=100,  # nb_agents, # TODO(xabier): fix when server side is ready (then should at least filter on agent_type==None)
        )
        agents = []
        for r in response:
            agent = AgentFactory.load_agent_from_api(r)
            if (
                agent.agent_type is None
            ):  # Filter out architect and genetic operator agents
                agents.append(agent)

        # TODO(xabier): random choice should be handled server-side
        return (
            random.choices(agents, k=nb_agents) if len(agents) >= nb_agents else agents
        )

    @classmethod
    @_handle_api_errors
    def get_cost(cls, forge_cycle_uuid: str) -> float:
        """Get spend information for a forge cycle.

        Args:
            forge_cycle_uuid: UUID of the forge cycle.

        Returns:
            Spent budget value.

        """
        forge_cycle_spend_output = cls._get_client().get_spend(
            forge_cycle_uuid=forge_cycle_uuid,
        )
        return forge_cycle_spend_output.spent_budget

    @classmethod
    @_handle_api_errors
    def end_forge_cycle(
        cls,
        forge_cycle_uuid: str,
        winning_agents: list["Agent"],
    ) -> None:
        """End a forge cycle."""
        agents_data = [
            build_agent_input_model(agent, forge_cycle_id=forge_cycle_uuid)
            for agent in winning_agents
        ]
        cls._get_client().end_forge_cycle(
            forge_cycle_uuid=forge_cycle_uuid,
            agents_data=agents_data,
        )


def get_sample_agent() -> "Agent":
    """Create a sample math-solving agent for testing/demo use.

    Returns:
        An Agent instance configured with a solver and verifier node.

    """

    class AgentInput(BaseModel):
        math_problem: str = Field(
            ...,
            description="The mathematical word problem to solve",
        )

    class AgentOutput(BaseModel):
        """The expected final output to the mathematical problem."""

        solution: int = Field(..., description="The solution to the problem.")

    shared_context_prompt = """
    Your are part of a multi-node agent that solves math problems.
    The agent has two main nodes: the solver node and the verifier node.
    The solver node solves the math problem and the verifier node verifies the solution
    given by the solver node. If it is incorrect, the verifier node provides insights
    back to the solver node so that it improves the solution.
    """

    solver_prompt = """
    Your are the Solver node. You must solve the given math problem.
    """

    solver_node = LLMNode(
        id="solver",
        name="Solver",
        purpose="solve the math problem",
        prompt=solver_prompt,
    )
    verifier_prompt = """
    You are the Verified node.
    Based on the solution provided by the Solver node,
    you must decide whether the solution is correct or not.
    If the solution is incorrect, explain why and provide insights back
    to the solver node so that it improves the solution.
    """

    verifier_node = LLMNode(
        id="verifier",
        name="Verifier",
        purpose="verify the math problem",
        prompt=verifier_prompt,
    )

    start_node = StartNode()
    end_node = EndNode()

    math_graph = Graph(shared_context_prompt=shared_context_prompt)

    # adding nodes
    math_graph.add_node(start_node)
    math_graph.add_node(solver_node)
    math_graph.add_node(verifier_node)
    math_graph.add_node(end_node)

    # adding edges
    # from start to solver
    math_graph.add_edge(Edge(start_node_id=start_node.id, end_node_id=solver_node.id))
    # from solver to verifier
    math_graph.add_edge(
        Edge(start_node_id=solver_node.id, end_node_id=verifier_node.id),
    )
    # from verifier to end,  if the condition is correct
    math_graph.add_edge(
        Edge(
            start_node_id=verifier_node.id,
            end_node_id=end_node.id,
            condition="correct",
        ),
    )
    # from verifier to solver, if the condition is incorrect
    math_graph.add_edge(
        Edge(
            start_node_id=verifier_node.id,
            end_node_id=solver_node.id,
            condition="incorrect",
        ),
    )

    math_graph_engine = AgentEngineFactory.create_engine(
        engine_type="langgraph_engine",
        agent_id="agent-" + str(uuid.uuid4()),
        configuration={
            "graph": math_graph.model_dump(),
            "input_model": AgentInput.model_json_schema(),
            "output_model": AgentOutput.model_json_schema(),
        },
        model_endpoint_id="azure/gpt-4o-mini",
    )

    # TODO(xabier): handle model_endpoint_id independently of the agent engine
    architect_agent = GraphUtils.get_architect_agent(
        model_endpoint_id="azure/gpt-4o-mini",
    )
    crossover_agent = GraphUtils.get_crossover_agent(
        model_endpoint_id="azure/gpt-4o-mini",
    )
    GraphUtils.get_mutation_agent(
        model_endpoint_id="azure/gpt-4o-mini",
    )

    math_agent_id = math_graph_engine.agent_id or "agent-" + str(uuid.uuid4())
    return Agent(
        name="Math Agent",
        description="An agent that solves math problems",
        agent_engine=math_graph_engine,
        id=math_agent_id,
        architect_agent_id=architect_agent.id,
        genetic_operator_agent_id=crossover_agent.id,
    )
