# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Documentation
- **MkDocs Integration**: Added comprehensive documentation site with MkDocs and Material theme
- **API Reference**: Auto-generated API documentation from Python docstrings (Google style)
- **User Guides**: Added guides for core concepts, creating agents, and building ecosystems
- **Getting Started**: Installation, quick start, and configuration guides
- **Examples**: Added example code for math problem solving, code generation, and ecosystem evolution
- **Docstrings**: Added Google-style docstrings across the codebase for full API documentation coverage

#### CI/CD
- **GitHub Actions CI**: Added comprehensive CI workflow (`ci.yml`)
  - Ruff formatting and linting
  - Mypy type checking
  - YAML and Docker linting
  - Test execution with pytest
  - Documentation build verification
  - Artifact upload for generated docs
- **Documentation Deployment**: Added automated docs deployment to GitHub Pages (`docs.yml`)
  - Automatic build on push to main
  - Concurrency control to avoid race conditions
  - Manual workflow dispatch support
- **Dependabot**: Added dependency update automation

#### Development Tools
- **Pre-commit Hooks**: Enhanced `.pre-commit-config.yaml` with type checking stage control
- **MkDocs Configuration**: Added `mkdocs.yml` with Material theme and mkdocstrings plugin
- **Project Configuration**: Added mkdocs, mkdocs-material, and mkdocstrings to dev dependencies in `pyproject.toml`

#### Code Improvements
- **System Agent IDs**: Added `SystemAgentId` enum in `ebiose/core/constants.py` to replace hardcoded UUIDs
  - `ARCHITECT`: `agent-54c2124d-a473-43e6-ae1c-24a217ff7607`
  - `CROSSOVER`: `agent-e2b8c849-5709-436d-b7eb-0e0d7e580724`
  - `MUTATION`: `agent-b0d53155-4525-4d4a-92c8-145426f4a4bf`
  - `ROUTING`: `agent-cb88834e-cb03-4cf9-b983-2b18fdbbcdc9`
  - `STRUCTURED_OUTPUT`: `agent-20419b21-ba04-4673-b72f-c798dba9e313`
- **LLM API Protocol**: Added `LLMCallConfigProtocol` for type-safe LLM call configuration
- **Import Organization**: Improved imports in LLM API modules with proper guard statements for optional dependencies
- **Code Quality**: Removed unnecessary `pass` statements (PIE790 violations)
- **Type Hints**: Enhanced type annotations across the codebase

#### Testing
- **API Contract Tests**: Added `test_api_contract.py` to verify LLM API refactoring
- **Code Node Security Tests**: Added `test_code_node_security.py` with security validation tests
- **LLM API Tests**: Enhanced `test_llm_api_initialization.py` with improved assertions

### Changed

#### Configuration
- **Ruff Config**: Reorganized ignore patterns for better readability
- **Mypy Config**: Reorganized settings with clearer grouping (strictest settings, type checking enforcement, advanced features)
- **CI Workflow**: Updated to use `curl` for `uv` installation instead of GitHub action
- **Dependabot Config**: Added manual stage control for type checking in pre-commit

#### Documentation Files
- Updated `.gitignore` to include `site/` directory (MkDocs output)
- Enhanced `.pre-commit-config.yaml` with manual workflow stage control

### Fixed

- **Routing Node Serialization**: Fixed `model_dump()` calls in LangGraph routing node for proper state serialization
- **Cloud Client Returns**: Improved return value handling in `add_api_key` and `self_add_api_key` methods
- **Imports**: Fixed import warnings in LLM API modules with suppression of Pydantic V1 deprecation warnings
- **Test Type Hints**: Added proper return type hints to test functions
- **Module Exports**: Added `__all__` to graph node package for explicit exports

### Technical Details

#### Documentation Architecture
- **mkdocstrings** plugin automatically extracts docstrings from Python code
- **Google-style docstrings** required across all modules
- API pages use `::: module.path` syntax for auto-documentation
- Full type information preserved and displayed in generated docs

#### CI/CD Pipeline
- **Lint & Test** runs on all PRs to main
- **Deploy Docs** runs only on push to main
- Artifacts uploaded for manual inspection
- GitHub Pages deployment with automatic URL configuration

---

## [0.1.0] - 2025-06-01

Initial beta release with foundational features.

### Features
- Architect agents for designing other agents
- Darwinian evolutionary engine
- LangGraph-based agent orchestration
- Cloud integration with LiteLLM support

[Unreleased]: https://github.com/ebiose-ai/ebiose/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ebiose-ai/ebiose/releases/tag/v0.1.0
