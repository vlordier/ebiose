# Installation

## Requirements

- Python 3.12 or higher
- pip or uv package manager

## From PyPI (Recommended)

```bash
pip install ebiose
```

Or with uv:

```bash
uv pip install ebiose
```

## From Source

Clone the repository:

```bash
git clone https://github.com/ebiose-ai/ebiose.git
cd ebiose
```

Install with development dependencies:

```bash
uv sync --dev
```

## Setting Up LLM Providers

Ebiose supports multiple LLM providers. Set up your preferred provider:

### OpenAI

```bash
export OPENAI_API_KEY="your-api-key"
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Azure

```bash
export AZURE_API_KEY="your-api-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com"
export AZURE_API_VERSION="2024-02-15-preview"
```

### Local Models (Ollama)

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
```

See the [LLM API Reference](../api/llm_api.md) for more providers.

## Verification

Verify your installation:

```python
import ebiose
print(ebiose.__version__)
```

You should see the version number without errors.

## Next Steps

- [Quick Start Guide](quick-start.md)
- [Core Concepts](../guide/concepts.md)
