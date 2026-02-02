"""Graph node implementations.

Provides different node types for building computational graphs,
including LLM nodes, code execution nodes, routing nodes, and more.
"""

import importlib
import random
from functools import reduce
from typing import Any

from ebiose.core.engines.graph_engine.nodes.llm_node import LLMNode
from ebiose.core.engines.graph_engine.nodes.node import BaseNode, EndNode, StartNode
from ebiose.core.engines.graph_engine.nodes.pydantic_validator_node import (
    PydanticValidatorNode,
)
from ebiose.core.engines.graph_engine.nodes.routing_node import RoutingNode

__all__ = [
    "BaseNode",
    "EndNode",
    "LLMNode",
    "PydanticValidatorNode",
    "RoutingNode",
    "StartNode",
    "get_all_subclasses",
]


def get_all_subclasses(cls: type) -> list[type]:
    """Get all subclasses of a class recursively.

    Its purpose is to provide the Union type representing all node types, in use in the Graph class.
    """
    all_subclasses = []
    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return all_subclasses


# Import the module containing the node types
nodes_module = importlib.import_module("ebiose.core.engines.graph_engine.nodes")

# Get all subclasses of BaseNode
node_types = get_all_subclasses(BaseNode)

# Build a list of names of node types
node_types_names = [node_type.__name__ for node_type in node_types]

# Build a map from string names to types
node_types_map = {node_type.__name__: node_type for node_type in node_types}

# Remove BaseNode itself if it's in the list
if BaseNode in node_types:
    node_types.remove(BaseNode)


# Create the NodeTypes union from the node types list
# This creates a union type dynamically at runtime for all node subclasses
# The reduce operation creates a union type, which mypy cannot properly type
NodeTypes: Any = reduce(lambda acc, t: acc | t, node_types)  # type: ignore[arg-type, return-value]


def get_node_types_docstrings(node_types_names: list) -> str:
    """Get the docstring of each node type to pass in the prompts."""
    docstrings_list = []
    for node_type_name in node_types_names:
        node_type = node_types_map.get(node_type_name)
        if node_type:
            docstring = node_type.__doc__
            if docstring:
                docstrings_list.append(f"**{node_type_name}**:\n{docstring}\n")
    return "\n".join(docstrings_list)


def get_n_llm_nodes_constraint_string(
    *,
    random_n_llm_nodes: bool,
    max_llm_nodes: int,
) -> str:
    """Get the constraint string for the number of LLM nodes in the graph."""
    if random_n_llm_nodes:
        return f"Be careful : The number of LLM nodes in the graph must be of {random.randint(1, max_llm_nodes)} exactly."

    return f"Be careful : Do not exceed {max_llm_nodes} LLM nodes in the graph."
