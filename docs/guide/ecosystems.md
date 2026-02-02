# Ecosystems

Learn how to create and manage agent ecosystems.

## What is an Ecosystem?

An ecosystem is a collection of agents that:

- Co-evolve through generations
- Compete on performance metrics
- Undergo mutation and crossover
- Specialize in different tasks
- Share resources and knowledge

## Creating an Ecosystem

```python
from ebiose.core.ecosystem import Ecosystem
from ebiose.core.agent import Agent

ecosystem = Ecosystem(
    id="ecosystem-1",
    name="Math Solvers",
    description="A community of math-solving agents"
)

# Add agents
ecosystem.add_agent(agent1)
ecosystem.add_agent(agent2)
```

## Forge Cycles

Run evolutionary iterations:

```python
from ebiose.core.forge_cycle import ForgeCycle

forge_cycle = ForgeCycle(
    id="cycle-1",
    ecosystem=ecosystem,
    generation=1,
    task="Solve math problems",
    agents=ecosystem.agents
)

# Execute the cycle
new_agents = await forge_cycle.execute()
```

## Evolutionary Operations

### Mutation

Create variations of existing agents:

```python
from ebiose.backends.langgraph.engine.base_agents.mutation_agent import MutationAgent

mutant = MutationAgent.create(
    parent_agent=agent,
    llm_api=llm_api,
    mutation_type="temperature_change"
)
```

### Crossover

Combine traits from multiple parents:

```python
from ebiose.backends.langgraph.engine.base_agents.crossover_agent import CrossoverAgent

offspring = CrossoverAgent.create(
    parent_agents=[agent1, agent2],
    llm_api=llm_api
)
```

### Architecture Design

Design new agents for specific tasks:

```python
from ebiose.backends.langgraph.engine.base_agents.architect_agent import ArchitectAgent

new_agent = ArchitectAgent.create(
    task="Optimize code",
    llm_api=llm_api,
    ecosystem=ecosystem
)
```

## Performance Metrics

Track agent performance:

```python
# Evaluate an agent
fitness_score = await evaluate_agent(agent, test_cases)

# Store metrics
agent.fitness = fitness_score
agent.generation = current_generation
```

## Agent Selection

Select agents for breeding:

```python
# Top performing agents
elite = ecosystem.get_top_agents(count=5)

# Tournament selection
winner = ecosystem.tournament_selection(tournament_size=3)

# Rank-based selection
selected = ecosystem.rank_based_selection()
```

## Full Example

```python
import asyncio
from ebiose.core.ecosystem import Ecosystem
from ebiose.core.forge_cycle import ForgeCycle

async def run_evolution():
    # Create ecosystem
    ecosystem = Ecosystem(
        id="eco-1",
        name="Evolving Agents"
    )
    
    # Add initial agents
    for i in range(10):
        agent = create_agent(f"agent-{i}")
        ecosystem.add_agent(agent)
    
    # Run forge cycles
    for generation in range(5):
        cycle = ForgeCycle(
            ecosystem=ecosystem,
            generation=generation,
            task="Solve problems"
        )
        
        new_agents = await cycle.execute()
        ecosystem.agents = new_agents
        
        print(f"Generation {generation}: "
              f"Best fitness = {ecosystem.best_fitness}")

asyncio.run(run_evolution())
```

## Next Steps

- [Concepts Guide](concepts.md)
- [Creating Agents](agents.md)
- [API Reference](../api/core.md)
