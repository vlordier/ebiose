# Quick Start

Get up and running with Ebiose in 5 minutes.

## 1. Initialize an LLM API

First, set your API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Then initialize the LLM API:

```python
from ebiose.core.llm_api import LLMApi

llm_api = LLMApi.initialize(
    provider="openai",
    model="gpt-4o-mini"
)
```

## 2. Create an Agent Engine

```python
from ebiose.backends.langgraph.engine.langgraph_engine import LangGraphEngine
from ebiose.core.agent_engine_factory import AgentEngineFactory

engine = LangGraphEngine.from_config(
    agent_type="standard",
    llm_api=llm_api
)
```

## 3. Create an Agent

```python
from ebiose.core.agent import Agent

agent = Agent(
    id="solver-1",
    name="Problem Solver",
    description="Solves problems using LLMs",
    agent_engine=engine
)
```

## 4. Run the Agent

```python
import asyncio

async def main():
    result = await agent.run("Solve: 15 + 27")
    print(result)

asyncio.run(main())
```

## Next Steps

- [Explore Concepts](../guide/concepts.md)
- [Creating Agents Guide](../guide/agents.md)
- [API Reference](../api/core.md)

## Need Help?

- Check the [Examples](../examples.md)
- Review the [API Reference](../api/core.md)
- Open an [issue on GitHub](https://github.com/ebiose-ai/ebiose/issues)
