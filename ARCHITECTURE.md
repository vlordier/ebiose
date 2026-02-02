# Architecture Overview

This document provides a high-level overview of Ebiose's system architecture and key components.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Ebiose Framework                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │   User Code      │  │  Cloud API       │                 │
│  │  (Agents,        │  │  (Optional)      │                 │
│  │   Forges)        │  │                  │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                           │
│           └──────────┬──────────┘                           │
│                      │                                      │
│           ┌──────────▼──────────┐                           │
│           │   Core Module       │                           │
│           │  ┌────────────────┐ │                           │
│           │  │ Agent          │ │  - Agent execution        │
│           │  │ AgentEngine    │ │  - Evolution cycles       │
│           │  │ AgentForge     │ │  - Ecosystem management   │
│           │  │ Ecosystem      │ │  - LLM API abstraction    │
│           │  │ ForgeCycle     │ │                           │
│           │  └────────────────┘ │                           │
│           └──────────┬───────────┘                           │
│                      │                                      │
│           ┌──────────▼──────────────┐                        │
│           │  Graph Engine Module     │                       │
│           │  ┌────────────────────┐ │                        │
│           │  │ Graph              │ │  - Computational DAG    │
│           │  │ Nodes (LLM, Code,  │ │  - Node execution       │
│           │  │  Router, etc.)     │ │  - State management     │
│           │  │ Edges              │ │  - Condition routing    │
│           │  └────────────────────┘ │                        │
│           └──────────┬───────────────┘                        │
│                      │                                      │
│           ┌──────────▼──────────┐                           │
│           │  Backend Module      │                           │
│           │  ┌────────────────┐ │                           │
│           │  │ LangGraph      │ │  - Agent orchestration    │
│           │  │ (Graph-based   │ │  - State transitions      │
│           │  │  execution)    │ │  - Tool calling           │
│           │  └────────────────┘ │                           │
│           └──────────┬───────────┘                           │
│                      │                                      │
│           ┌──────────▼──────────┐                           │
│           │  LLM API Module      │                           │
│           │  ┌────────────────┐ │                           │
│           │  │ LLM Abstraction│ │  - Multi-provider support │
│           │  │ (OpenAI,       │ │  - Token counting         │
│           │  │  Anthropic,    │ │  - Cost tracking          │
│           │  │  Azure, etc.)  │ │  - Message formatting     │
│           │  └────────────────┘ │                           │
│           └──────────┬───────────┘                           │
│                      │                                      │
│           ┌──────────▼──────────┐                           │
│           │  Tools Module        │                           │
│           │  ┌────────────────┐ │                           │
│           │  │ Embeddings     │ │  - Vector operations      │
│           │  │ JSON Schema    │ │  - Schema conversion      │
│           │  │ Type Utils     │ │  - Type inspection        │
│           │  └────────────────┘ │                           │
│           └──────────────────────┘                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent (`ebiose/core/agent.py`)
- Represents an autonomous entity in the ecosystem
- Encapsulates an agent engine and configuration
- Can be serialized/deserialized for persistence
- Has unique ID, name, and description

### 2. Agent Engine (`ebiose/core/agent_engine.py`)
- Executes agents through a computational graph
- Manages state transitions and message flow
- Handles tool calling and LLM interactions
- Currently implemented by LangGraph backend

### 3. Graph Engine (`ebiose/core/engines/graph_engine/`)
- Defines the computational graph structure
- Supports different node types (LLM, Code, Router, Validator, etc.)
- Manages edges with conditional routing
- Executes nodes sequentially based on graph topology

### 4. LLM API (`ebiose/core/llm_api.py`)
- Unified interface for multiple LLM providers
- Abstracts away provider-specific details
- Tracks token usage and costs
- Supports both local and cloud modes

### 5. Agent Forge (`ebiose/core/agent_forge.py`)
- Manages evolutionary optimization of agents
- Defines fitness evaluation criteria
- Coordinates forge cycles
- Handles agent persistence and versioning

### 6. Ecosystem (`ebiose/core/ecosystem.py`)
- Container for agents that evolve together
- Tracks agent performance metrics
- Implements agent selection strategies
- Manages ecosystem-wide state

### 7. Forge Cycle (`ebiose/core/forge_cycle.py`)
- Executes one iteration of evolutionary algorithm
- Implements genetic operators (mutation, crossover)
- Manages generation counter and agent selection
- Orchestrates architect, crossover, and mutation agents

## Execution Flow

### Single Agent Execution
```
User Input
    ↓
Agent.run()
    ↓
AgentEngine (Graph)
    ├─ Execute Start Node
    ├─ Execute LLM Node(s)
    ├─ Execute Tool Node(s) [if needed]
    ├─ Conditional Routing
    └─ Execute End Node
    ↓
Output
```

### Evolutionary Cycle
```
Ecosystem with N agents
    ↓
Evaluate each agent on tasks
    ↓
Select top performers
    ↓
Generate variants via:
    ├─ Mutation (modify existing agent)
    ├─ Crossover (combine two agents)
    └─ Architecture Design (create new agent)
    ↓
Replace worst agents with variants
    ↓
Updated Ecosystem (Generation N+1)
```

## Data Flow

### State Representation
- Uses Pydantic BaseModel for type-safe state
- State flows through graph nodes
- Each node receives input state and produces output state
- State can include messages, context, and execution results

### Message Types
- **HumanMessage**: User input
- **AIMessage**: LLM output, may include tool calls
- **ToolMessage**: Tool execution results
- **SystemMessage**: System context and instructions

## Extensibility Points

### Custom Node Types
```python
from ebiose.core.engines.graph_engine.nodes.node import BaseNode

class CustomNode(BaseNode):
    async def call_node(self, state, config):
        # Your custom logic
        return output_state
```

### Custom LLM Backends
```python
from ebiose.core.llm_api import LLMApi

class CustomLLMApi(LLMApi):
    @classmethod
    async def process_llm_call(cls, config):
        # Your backend implementation
        return message
```

### Custom Agent Engines
```python
from ebiose.core.agent_engine import AgentEngine

class CustomEngine(AgentEngine):
    async def run(self, input_model, **kwargs):
        # Your engine implementation
        return output
```

## Module Organization

```
ebiose/
├── core/                    # Core abstractions
│   ├── agent.py
│   ├── agent_engine.py
│   ├── agent_forge.py
│   ├── ecosystem.py
│   ├── forge_cycle.py
│   ├── llm_api.py
│   ├── model_endpoint.py
│   ├── events.py
│   └── engines/
│       └── graph_engine/    # Graph execution engine
│           ├── graph.py
│           ├── edge.py
│           └── nodes/
├── backends/
│   └── langgraph/           # LangGraph backend implementation
│       ├── llm_api.py
│       └── engine/
├── cloud_client/            # Cloud API integration
├── tools/                   # Utilities and helpers
└── llm_api/                # LLM provider implementations
```

## Key Design Principles

1. **Type Safety**: Full type hints with mypy strict checking
2. **Composability**: Agents and engines are composable building blocks
3. **Abstraction**: Multiple backends can implement the same interfaces
4. **Extensibility**: Easy to add custom nodes, engines, and LLM providers
5. **Persistence**: Agents can be serialized and restored
6. **Observability**: Events and logging throughout execution
7. **Evolutionary**: Built-in support for genetic algorithms and agent optimization

## Technology Stack

- **LangGraph**: Agent orchestration and graph execution
- **Pydantic**: Type-safe data validation
- **LiteLLM**: Multi-provider LLM abstraction
- **LangChain**: LLM components and tools
- **FastAPI** (optional): Cloud API client
- **MkDocs**: Documentation generation

## Performance Considerations

- **Concurrency**: Async/await throughout for non-blocking I/O
- **Caching**: Graph structures and model endpoints cached in memory
- **Token Optimization**: Tracks and minimizes token usage
- **Cost Tracking**: Monitors and reports LLM costs per cycle
- **Lazy Loading**: Optional dependencies loaded only when needed
