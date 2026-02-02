# Creating Agents

Learn how to create and configure agents in Ebiose.

## Basic Agent Creation

```python
from ebiose.core.agent import Agent

agent = Agent(
    id="solver-1",
    name="Math Solver",
    description="Solves mathematical problems",
    agent_engine=your_engine  # See below
)
```

## Setting Up the Engine

### Option 1: LangGraph Engine (Recommended)

```python
from ebiose.backends.langgraph.engine.langgraph_engine import LangGraphEngine
from ebiose.core.llm_api import LLMApi

# Initialize LLM
llm_api = LLMApi.initialize(provider="openai", model="gpt-4o-mini")

# Create engine
engine = LangGraphEngine.from_config(
    agent_type="standard",
    llm_api=llm_api,
    temperature=0.7
)

# Create agent
agent = Agent(
    id="agent-1",
    name="Assistant",
    description="A helpful assistant",
    agent_engine=engine
)
```

### Option 2: Factory Pattern

```python
from ebiose.core.agent_engine_factory import AgentEngineFactory

engine = AgentEngineFactory.create(
    agent_type="standard",
    llm_api=llm_api
)
```

## Running an Agent

### Async Execution

```python
import asyncio

async def main():
    result = await agent.run("What is the capital of France?")
    print(result)

asyncio.run(main())
```

### With Additional Context

```python
result = await agent.run(
    input="Solve this problem",
    context={"domain": "mathematics"}
)
```

## Agent Types

Ebiose supports different agent types for different purposes:

### Standard Agent

General-purpose agent for most tasks.

```python
engine = LangGraphEngine.from_config(
    agent_type="standard",
    llm_api=llm_api
)
```

### Architect Agent

Designs other agents based on task requirements.

```python
engine = LangGraphEngine.from_config(
    agent_type="architect",
    llm_api=llm_api
)
```

### Mutation Agent

Generates variations of existing agents.

```python
engine = LangGraphEngine.from_config(
    agent_type="mutation",
    llm_api=llm_api
)
```

### Crossover Agent

Combines traits from multiple agents.

```python
engine = LangGraphEngine.from_config(
    agent_type="crossover",
    llm_api=llm_api
)
```

## Serialization

Save and load agent configurations:

```python
# Get configuration
config = agent.serialize_configuration()

# Load from configuration
new_agent = Agent.from_config(config)
```

## Next Steps

- [Building Ecosystems](ecosystems.md)
- [API Reference](../api/agents.md)
