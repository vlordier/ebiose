# Complete Violation Reference List

## Statistics Summary

- **D104** (Package): 12 files needing module docstrings
- **D101** (Classes): 57 violations across multiple files
- **D102** (Methods): 61 violations across multiple files
- **D103** (Functions): 13 violations across multiple files
- **D107** (__init__): 5 violations
- **D105** (Magic methods): 3 violations
- **TOTAL**: ~151 violations

---

## D104 - Package/Module Docstrings (12 files)

These files need module-level docstrings at the top:

1. `ebiose/__init__.py` - Main package
2. `ebiose/backends/__init__.py` - Backends package
3. `ebiose/backends/langgraph/__init__.py` - LangGraph backend
4. `ebiose/backends/langgraph/engine/__init__.py` - LangGraph engine
5. `ebiose/backends/langgraph/engine/base_agents/__init__.py` - Base agents
6. `ebiose/cloud_client/__init__.py` - Cloud client
7. `ebiose/core/__init__.py` - Core package
8. `ebiose/core/engines/__init__.py` - Engines package
9. `ebiose/core/engines/graph_engine/__init__.py` - Graph engine
10. `ebiose/core/engines/graph_engine/nodes/__init__.py` - Graph nodes
11. `ebiose/llm_api/__init__.py` - LLM API package
12. `ebiose/tools/__init__.py` - Tools package

**Add at the top of each file:**
```python
"""Brief description of what this module/package contains."""
```

---

## D101 - Class Docstrings (57 violations)

### By Module:

**ebiose/backends/langgraph/engine/agent_node.py**
- Line 14: `InputState`
- Line 18: `OutputState`
- Line 22: `LangGraphAgentNode`

**ebiose/backends/langgraph/engine/base_agents/architect_agent.py**
- Line 20: `AgentInput`
- Line 28: `AgentOutput`

**ebiose/backends/langgraph/engine/base_agents/crossover_agent.py**
- Line 20: `AgentInput`
- Line 31: `AgentOutput`

**ebiose/backends/langgraph/engine/base_agents/mutation_agent.py**
- Line 20: `AgentInput`
- Line 31: `AgentOutput`

**ebiose/backends/langgraph/engine/base_agents/routing_agent.py**
- Line 34: `AgentInput`
- Line 39: `AgentOutput`

**ebiose/backends/langgraph/engine/langgraph_engine.py**
- Line 44: `LangGraphEngine`

**ebiose/backends/langgraph/engine/llm_node.py**
- Line 30: `InputState`
- Line 34: `OutputState`
- Line 37: `LLMCallError`

**ebiose/cloud_client/client.py**
- Various: APIBaseModel, ResponseValidator, APIResponse, SingleResponse, ListResponse, etc.

**ebiose/core/agent.py**
- Various: Agent, AgentType, AgentInputModel, etc.

**ebiose/core/agent_engine.py**
- Various: AgentEngine related classes

**ebiose/core/agent_engine_factory.py**
- Various: Factory classes

**ebiose/core/agent_forge.py**
- AgentForge class

**ebiose/core/ecosystem.py**
- Ecosystem class

**ebiose/core/events.py**
- All Event classes

**ebiose/core/forge_cycle.py**
- ForgeCycle class and related models

**ebiose/core/llm_api.py**
- LLMApi, LLMAPIConfig classes

**ebiose/core/model_endpoint.py**
- ModelEndpoint, ModelEndpoints classes

**ebiose/core/engines/graph_engine/graph.py**
- Graph, Node, Edge classes

**ebiose/core/engines/graph_engine/graph_engine.py**
- GraphEngine class

**ebiose/core/engines/graph_engine/nodes/node.py**
- BaseNode, StartNode, EndNode classes

**ebiose/core/engines/graph_engine/nodes/code_node.py**
- CodeNode class

**ebiose/core/engines/graph_engine/nodes/llm_node.py**
- LLMNode class

**ebiose/core/engines/graph_engine/nodes/pydantic_validator_node.py**
- PydanticValidatorNode class

**ebiose/core/engines/graph_engine/nodes/routing_node.py**
- RoutingNode class

**ebiose/core/engines/graph_engine/nodes/agent_node.py**
- AgentNode class

**ebiose/core/engines/graph_engine/utils.py**
- GraphUtils class

**ebiose/tools/embedding_helper.py**
- Embedding-related classes

**ebiose/tools/json_schema_to_pydantic.py**
- Schema conversion classes

---

## D102 - Method Docstrings (61 violations)

These are methods within classes that need docstrings. Examples include:

**ebiose/backends/langgraph/engine/agent_node.py**
- `call_node()` method in LangGraphAgentNode

**ebiose/core/agent.py**
- Various methods in Agent class
- Run, evaluate, serialize methods

**ebiose/core/agent_forge.py**
- `generate_agent()` and related methods

**ebiose/core/ecosystem.py**
- Methods for managing ecosystem

**ebiose/core/engines/graph_engine/graph.py**
- Graph manipulation and execution methods

**ebiose/core/engines/graph_engine/nodes/**
- `call_node()` methods in all node classes
- Other node-specific methods

---

## D103 - Function Docstrings (13 violations)

Top-level functions that need docstrings:

1. `ebiose/backends/langgraph/engine/base_agents/architect_agent.py:113`
   - `init_architect_agent()`

2. `ebiose/backends/langgraph/engine/base_agents/crossover_agent.py:80`
   - `init_crossover_agent()`

3. `ebiose/backends/langgraph/engine/base_agents/mutation_agent.py:82`
   - `init_mutation_agent()`

4. `ebiose/backends/langgraph/engine/base_agents/routing_agent.py:43`
   - `init_routing_agent()`

5. `ebiose/backends/langgraph/engine/base_agents/structured_output_agent.py:34`
   - `init_structured_output_agent()`

6. `ebiose/core/engines/graph_engine/nodes/__init__.py`
   - `get_all_subclasses()`

7. `ebiose/tools/json_schema_to_pydantic.py`
   - `create_pydantic_model_from_schema()`

And 6 more utility functions...

---

## D107 - __init__ Method Docstrings (5 violations)

Constructor methods that need docstrings:

1. `ebiose/backends/langgraph/engine/llm_node.py`
   - `LLMCallError.__init__()`

2. And 4 more in various classes...

---

## D105 - Magic Method Docstrings (3 violations)

Special methods needing docstrings:

1. `__repr__()` - Object representation methods
2. `__str__()` - String representation methods
3. Other `__xxx__()` magic methods

---

## Implementation Guide

### Quick Template

**For packages (D104):**
```python
"""Package name and brief description.

More details about what's in this package.
"""
```

**For classes (D101):**
```python
class ClassName:
    """One-line description.
    
    More detailed description.
    
    Attributes:
        attr1: Description.
    """
```

**For methods (D102):**
```python
def method_name(self, param) -> ReturnType:
    """One-line description.
    
    Args:
        param: Description.
    
    Returns:
        Description.
    """
```

**For functions (D103):**
```python
def function_name(param) -> ReturnType:
    """One-line description.
    
    Args:
        param: Description.
    
    Returns:
        Description.
    """
```

---

## Verification

To check progress:
```bash
ruff check ebiose --select D1
```

Once all docstrings are added, you should see **0 violations**.

To build and view documentation:
```bash
mkdocs build && mkdocs serve
```

Visit `http://localhost:8000` to see the auto-generated documentation.
