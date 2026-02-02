"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from typing import Literal

from ebiose.core.engines.graph_engine.nodes.node import BaseNode


class PydanticValidatorNode(BaseNode):
    """Validates state against Pydantic models.

    The PydanticValidatorNode is used to validate the state at a specific point in
    the graph execution against a Pydantic model, ensuring data integrity and correctness.
    """

    type: Literal["PydanticValidatorNode"] = "PydanticValidatorNode"
