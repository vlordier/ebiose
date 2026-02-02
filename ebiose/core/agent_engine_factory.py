"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

# core/agentEngineFactory.py
from __future__ import annotations

from typing import TYPE_CHECKING

from ebiose.backends.langgraph.engine.langgraph_engine import LangGraphEngine
from ebiose.core.model_endpoint import ModelEndpoints

if TYPE_CHECKING:
    from ebiose.core.agent_engine import AgentEngine


class AgentEngineFactory:
    """Factory for creating agent execution engines.

    Provides methods to instantiate different types of agent engines
    based on configuration and type specifications.
    """

    @staticmethod
    def create_engine(
        engine_type: str,
        agent_id: str,
        configuration: dict,
        model_endpoint_id: str | None = None,
    ) -> AgentEngine:
        """Create an agent engine of the specified type.

        Args:
            engine_type: Type of engine to create (e.g., 'langgraph_engine').
            agent_id: ID of the agent using this engine.
            configuration: Engine configuration dictionary.
            model_endpoint_id: Optional LLM model endpoint ID.

        Returns:
            Configured AgentEngine instance.

        Raises:
            ValueError: If engine_type is not recognized.

        """
        if engine_type == "langgraph_engine":
            if model_endpoint_id is None:
                model_endpoint_id = ModelEndpoints.get_default_model_endpoint_id()
            return LangGraphEngine(
                agent_id=agent_id,
                configuration=configuration,
                model_endpoint_id=model_endpoint_id,
                input_model=None,
                output_model=None,
                graph=None,
            )
        msg = f"Unknown engine type: {engine_type}"
        raise ValueError(msg)
