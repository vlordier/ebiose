# Contributing

Thank you for your interest in contributing to Ebiose!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ebiose.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Push to your fork
6. Create a Pull Request

Before you start, please review:
- [ARCHITECTURE.md](https://github.com/ebiose-ai/ebiose/blob/main/ARCHITECTURE.md) - System design and components
- [SECURITY.md](https://github.com/ebiose-ai/ebiose/blob/main/SECURITY.md) - Security best practices and vulnerability reporting

## Development Setup

```bash
# Clone and enter directory
git clone https://github.com/ebiose-ai/ebiose.git
cd ebiose

# Install development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_llm_api_initialization.py

# Run with coverage
uv run pytest --cov=ebiose
```

## Code Quality

We maintain high code quality standards:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check --fix .

# Type checking
uv run mypy .

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## Documentation

We use MkDocs with mkdocstrings for documentation:

```bash
# Build docs locally
uv run mkdocs serve

# Build static docs
uv run mkdocs build
```

## Commit Guidelines

- Use clear, descriptive commit messages
- Reference issues when applicable: `Fixes #123`
- Follow conventional commits: `feat:`, `fix:`, `docs:`, etc.

## Pull Request Process

1. Ensure all tests pass: `uv run pytest`
2. Ensure code is formatted: `uv run ruff format .`
3. Ensure types are correct: `uv run mypy .`
4. Update documentation as needed
5. Add tests for new functionality
6. Request review from maintainers

## Code Style

- Follow PEP 8
- Use type hints for all function parameters and returns
- Write docstrings in Google style format
- Keep functions focused and well-named
- Write tests for new features

## Docstring Format

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    Longer description if needed. Can span multiple lines.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When this error occurs
        
    Example:
        >>> my_function("test", 42)
        True
    """
    pass
```

## Questions?

- Open an [issue](https://github.com/ebiose-ai/ebiose/issues)
- Ask on [GitHub Discussions](https://github.com/ebiose-ai/ebiose/discussions)
- Check existing documentation

Thank you for contributing!
