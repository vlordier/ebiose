"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import json
import traceback
from abc import abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar, cast

from langfuse import observe
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

F = TypeVar("F", bound=Callable[..., Any])
_ObserveDecorator = Callable[..., Callable[[F], F]]
_observe_typed = cast("_ObserveDecorator", observe)


class AgentEngineRunError(Exception):
    """Custom exception for errors during agent run."""

    def __init__(
        self,
        message: str,
        original_exception: Exception | None = None,
        agent_identifier: str | None = None,
    ) -> None:
        """Initialize the agent engine run error.

        Args:
            message: Error message.
            original_exception: Underlying exception, if any.
            agent_identifier: Optional agent identifier.

        """
        super().__init__(message)
        self.original_exception = original_exception
        self.agent_identifier = agent_identifier

    def __str__(self) -> str:
        """Get string representation of the error with full traceback information.

        Returns:
            Formatted error message with original exception traceback.

        """
        error_msg = "AgentRunError"
        if self.agent_identifier:
            error_msg += f" (Agent: {self.agent_identifier})"
        error_msg += f": {super().__str__()}"
        if self.original_exception:
            orig_traceback = traceback.format_exception(
                type(self.original_exception),
                self.original_exception,
                self.original_exception.__traceback__,
            )
            error_msg += f"\n--- Caused by ---\n{''.join(orig_traceback)}"
        return error_msg


class AgentEngine(BaseModel):
    """Base class for all agent engines."""

    engine_type: str
    agent_id: str | None = None
    configuration: dict | None = None
    input_model: type[BaseModel] | None = None
    output_model: type[BaseModel] | None = None
    model_endpoint_id: str | None = None
    tags: list[str] | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Allows initializing with snake_case names
    )

    async def run(
        self,
        agent_input: BaseModel,
        master_agent_id: str,
        forge_cycle_id: str | None = None,
        **kwargs: dict[str, Any],
    ) -> BaseModel:
        """Run the agent engine with the given input."""
        try:
            result = await self._run_implementation(
                agent_input,
                master_agent_id,
                forge_cycle_id,
                **kwargs,
            )
            return cast("BaseModel", result)
        except Exception as e:
            raise AgentEngineRunError(
                message="Error during agent engine run",
                original_exception=e,
                agent_identifier=self.agent_id,
            ) from e

    def serialize_configuration(self) -> str:
        """Serialize engine configuration to JSON string format.

        Returns:
            JSON string representation of the engine configuration.

        """
        return json.dumps(self.configuration or {})

    @_observe_typed(name="run_agent_engine")
    @abstractmethod
    async def _run_implementation(
        self,
        agent_input: BaseModel,
        master_agent_id: str,
        forge_cycle_id: str | None = None,
        **kwargs: dict[str, Any],
    ) -> BaseModel:
        """Run the agent engine."""
