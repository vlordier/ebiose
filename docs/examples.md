# Examples

## Math Problem Solving

Solve mathematical problems using an evolutionary ecosystem.

```python
import asyncio
from ebiose.core.agent import Agent
from ebiose.core.llm_api import LLMApi
from ebiose.backends.langgraph.engine.langgraph_engine import LangGraphEngine

async def main():
    # Initialize LLM
    llm_api = LLMApi.initialize(
        provider="openai",
        model="gpt-4o-mini"
    )
    
    # Create agent
    engine = LangGraphEngine.from_config(
        agent_type="standard",
        llm_api=llm_api
    )
    
    agent = Agent(
        id="math-solver",
        name="Math Solver",
        description="Solves mathematical problems",
        agent_engine=engine
    )
    
    # Run the agent
    result = await agent.run("Solve: 2x + 5 = 13")
    print(result)

asyncio.run(main())
```

## Code Generation

Generate code using agents.

```python
async def generate_code():
    llm_api = LLMApi.initialize(provider="openai", model="gpt-4o-mini")
    
    engine = LangGraphEngine.from_config(
        agent_type="standard",
        llm_api=llm_api
    )
    
    coder = Agent(
        id="code-gen",
        name="Code Generator",
        description="Generates Python code",
        agent_engine=engine
    )
    
    code = await coder.run("Write a function to calculate Fibonacci")
    print(code)
```

## Ecosystem Evolution

Run an evolutionary algorithm on a population of agents.

```python
async def evolve_agents():
    from ebiose.core.ecosystem import Ecosystem
    from ebiose.core.forge_cycle import ForgeCycle
    
    # Create ecosystem
    ecosystem = Ecosystem(
        id="eco-1",
        name="Evolving Solvers"
    )
    
    # Add initial agents
    for i in range(5):
        engine = LangGraphEngine.from_config(
            agent_type="standard",
            llm_api=llm_api
        )
        agent = Agent(
            id=f"agent-{i}",
            name=f"Agent {i}",
            agent_engine=engine
        )
        ecosystem.add_agent(agent)
    
    # Run forge cycles
    for gen in range(3):
        cycle = ForgeCycle(
            id=f"cycle-{gen}",
            ecosystem=ecosystem,
            generation=gen
        )
        new_agents = await cycle.execute()
        print(f"Generation {gen} complete")

asyncio.run(evolve_agents())
```

## More Examples

See the [examples/](https://github.com/ebiose-ai/ebiose/tree/main/examples) directory in the repository for more complete examples.

### Available Examples

- **Math Forge**: Evolutionary system for creating math problem solvers
- **Code Nodes**: Safe code execution within agents
- **LLM Initialization**: Various LLM provider configurations

## API Reference

See the [API Reference](api/core.md) for detailed documentation of all modules and classes.
