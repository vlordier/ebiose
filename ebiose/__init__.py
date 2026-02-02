"""Ebiose: Evolutionary ecosystem for AI agents.

Ebiose is a comprehensive framework for creating, evolving, and optimizing AI agents
through evolutionary algorithms. It provides tools for agent generation, ecosystem
management, and multi-agent coordination.

Main Components:
    core: Core agent and ecosystem functionality
    backends: Implementation backends (LangGraph, etc.)
    cloud_client: Cloud API client for remote execution
    tools: Utility functions and helpers
    llm_api: LLM API abstraction layer

Example:
    >>> from ebiose.core import Agent, Ecosystem
    >>> ecosystem = Ecosystem()
    >>> agents = await ecosystem.generate_agents()

"""
