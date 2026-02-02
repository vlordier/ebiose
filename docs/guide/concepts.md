# Core Concepts

## Agents

An **Agent** is the fundamental building block of Ebiose. It represents an autonomous entity that:

- Has a unique identity and configuration
- Uses an LLM to process inputs and generate outputs
- Maintains state through the execution graph
- Can be part of an ecosystem

### Agent Components

- **Agent Engine**: The execution engine (LangGraph, etc.)
- **LLM API**: The language model interface
- **Graph**: The computational graph defining agent behavior
- **Configuration**: Serializable configuration for persistence

## Agent Engines

An **Agent Engine** orchestrates the execution of an agent through a graph of nodes:

- **Nodes**: Processing units (LLM calls, validation, tool use, etc.)
- **Edges**: Connections between nodes with conditions
- **State**: Shared state across the graph execution

Ebiose provides the `LangGraphEngine` powered by LangGraph.

## Ecosystems

An **Ecosystem** is a collection of agents that evolve together:

- Agents compete and cooperate
- Evolutionary algorithms generate new agents
- Metrics track agent performance
- Agents can specialize in different tasks

## Forge Cycles

A **Forge Cycle** runs one iteration of the evolutionary algorithm:

1. **Evaluation**: Measure agent performance on tasks
2. **Selection**: Choose high-performing agents
3. **Variation**: Create new agents via mutation and crossover
4. **Replacement**: Update the ecosystem with new agents

## LLM APIs

The **LLM API** provides a unified interface to language models:

- Works with multiple providers (OpenAI, Anthropic, Azure, etc.)
- Handles model initialization and calls
- Manages API keys and configuration
- Provides token counting and cost tracking

## Agent Forge

The **Agent Forge** coordinates evolutionary optimization:

- Manages forge cycles
- Tracks agent lineage
- Implements genetic operators
- Handles agent persistence

## Graph-Based Execution

Agents use directed acyclic graphs (DAGs) for execution:

```
[Input] → [LLM Node] → [Validator] → [Output]
            ↓
         [Tools]
```

Each node processes state and produces outputs, enabling:

- Complex multi-step reasoning
- Conditional branching
- Tool use and integration
- Error recovery and loops

## State Models

State is represented using Pydantic models:

- Type-safe state representation
- Validation at each step
- Serializable for persistence
- Full IDE support

## Next Steps

- [Creating Agents](agents.md)
- [Building Ecosystems](ecosystems.md)
- [API Reference](../api/core.md)
