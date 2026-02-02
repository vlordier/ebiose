"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_serializer,
)

from ebiose.core.agent_engine import AgentEngine
from ebiose.tools.json_schema_to_pydantic import create_pydantic_model_from_schema

if TYPE_CHECKING:
    from ebiose.core.engines.graph_engine.graph import Graph


class GraphEngine(AgentEngine):
    """Graph-based agent engine with serialized graph configuration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    engine_type: str = "graph_engine"
    input_model: type[BaseModel] | None = Field(None)
    output_model: type[BaseModel] | None = Field(None)
    model_endpoint_id: str | None = None
    graph: Graph | None = Field(None)

    @model_serializer
    def _serialize_graph_engine(self) -> dict:
        """Serialize the graph engine into a configuration payload."""
        return {
            "engine_type": self.engine_type,
            "configuration": self.serialize_configuration(),
        }

    def serialize_configuration(self) -> str:
        """Serialize graph engine configuration to JSON.

        Returns:
            JSON string representation of the engine configuration.

        """
        return json.dumps(
            {
                "input_model": self.input_model.model_json_schema()
                if self.input_model is not None
                else {},
                "output_model": self.output_model.model_json_schema()
                if self.output_model is not None
                else {},
                "graph": self.graph.model_dump() if self.graph is not None else {},
                "model_endpoint_id": self.model_endpoint_id,
                "agent_id": self.agent_id,
            },
        )

    def _validate_input_output_models(
        self,
        model_name: str,
        io_model: dict[str, Any] | type[BaseModel],
    ) -> type[BaseModel]:
        """Validate or construct input/output models.

        Args:
            model_name: Name to use when constructing a model.
            io_model: Schema dict or Pydantic model class.

        Returns:
            A Pydantic model class.

        """
        if isinstance(io_model, dict):
            return create_pydantic_model_from_schema(
                schema=io_model,
                model_name=model_name,
            )
        return io_model

    def _serialize_input_output_models(
        self,
        io_model: type[BaseModel],
    ) -> dict[str, Any]:
        """Serialize a Pydantic model into a compact schema dictionary.

        Args:
            io_model: Pydantic model to serialize.

        Returns:
            Dictionary with model name and field metadata.

        """
        io_model_dict: dict[str, Any] = {"name": io_model.__name__, "fields": {}}
        for field_name, field in io_model.model_fields.items():
            annotation_name = "Any"
            if field.annotation:
                try:
                    annotation_name = getattr(
                        field.annotation,
                        "__name__",
                        str(field.annotation),
                    )
                except AttributeError:
                    annotation_name = str(field.annotation)
            io_model_dict["fields"][field_name] = (
                annotation_name,
                {"description": field.description},
            )
        return io_model_dict
