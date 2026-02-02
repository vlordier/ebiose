# Ebiose Documentation

Welcome to the Ebiose documentation! Ebiose is an automated evolutionary ecosystem for AI agents, enabling evolutionary computation and multi-agent optimization.

## What is Ebiose?

Ebiose provides a framework for:

- **Creating AI agents** with configurable LLM backends (OpenAI, Anthropic, local models, etc.)
- **Building agent ecosystems** with evolutionary algorithms
- **Running forge cycles** that generate new agents through mutation, crossover, and architectural design
- **Optimizing agents** based on performance metrics
- **Deploying agents** to cloud or local environments

## Key Features

- 🧬 **Evolutionary Algorithms**: Genetic operators for agent mutation and crossover
- 🔗 **LLM Agnostic**: Works with any LLM provider (OpenAI, Anthropic, Ollama, etc.)
- 📊 **Graph-Based Execution**: LangGraph-powered agent execution engine
- ☁️ **Cloud Integration**: Built-in cloud client for remote agent management
- 🛡️ **Type Safe**: Full type hints and strict mypy checking
- 🧪 **Well Tested**: Comprehensive test suite with CI/CD automation

## Quick Start

### Installation

```bash
pip install ebiose
```

### Create Your First Agent

```python
from ebiose.core.agent import Agent
from ebiose.core.llm_api import LLMApi

# Initialize LLM API
llm_api = LLMApi.initialize(
    provider="openai",
    model="gpt-4o-mini",
    api_key="your-api-key"
)

# Create an agent
agent = Agent(
    id="my-agent",
    name="Math Solver",
    description="Solves math problems",
    agent_engine=engine  # See guide for engine setup
)

# Run the agent
result = await agent.run("What is 2 + 2?")
```

## Documentation Structure

- **[Getting Started](getting-started/installation.md)**: Installation and basic setup
- **[User Guide](guide/concepts.md)**: Detailed concepts and usage patterns
- **[API Reference](api/core.md)**: Complete API documentation auto-generated from code
- **[Examples](examples.md)**: Real-world usage examples

## Next Steps

1. [Install Ebiose](getting-started/installation.md)
2. [Read the Quick Start](getting-started/quick-start.md)
3. [Explore the Examples](examples.md)
4. [Review the API Reference](api/core.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/ebiose-ai/ebiose/blob/main/CONTRIBUTING.md) for guidelines.

## License

Ebiose is released under the [License](https://github.com/ebiose-ai/ebiose/blob/main/LICENSE).
