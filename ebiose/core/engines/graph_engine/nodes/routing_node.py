"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from typing import Literal

from ebiose.core.engines.graph_engine.nodes.node import BaseNode


class RoutingNode(BaseNode):
    """Router node for directing execution flow based on conditions.

    The RoutingNode is used to implement conditional branching within the graph,
    allowing the execution flow to be directed to different nodes based on conditions
    or state values.
    """

    type: Literal["RoutingNode"] = "RoutingNode"
