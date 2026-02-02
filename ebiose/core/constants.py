"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from enum import Enum


class SystemAgentId(str, Enum):
    """Hardcoded IDs for singleton system agents to ensure deterministic identity."""

    ARCHITECT = "agent-54c2124d-a473-43e6-ae1c-24a217ff7607"
    CROSSOVER = "agent-e2b8c849-5709-436d-b7eb-0e0d7e580724"
    MUTATION = "agent-b0d53155-4525-4d4a-92c8-145426f4a4bf"
    ROUTING = "agent-cb88834e-cb03-4cf9-b983-2b18fdbbcdc9"
    STRUCTURED_OUTPUT = "agent-20419b21-ba04-4673-b72f-c798dba9e313"
