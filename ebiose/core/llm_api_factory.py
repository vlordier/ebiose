"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ebiose.backends.langgraph.llm_api import LangGraphLLMApi

if TYPE_CHECKING:
    from ebiose.core.llm_api import LLMApi, LLMAPIConfig


class LLMApiFactory:
    """Factory for creating and managing LLM API instances."""

    @classmethod
    def initialize(
        cls,
        mode: Literal["local", "cloud"],
        lite_llm_api_key: str | None = None,
        lite_llm_api_base: str | None = None,
        llm_api_config: LLMAPIConfig | None = None,
    ) -> type[LLMApi]:
        """Initialize the LLM API and return the instance."""
        return LangGraphLLMApi.initialize(
            mode,
            lite_llm_api_key,
            lite_llm_api_base,
            llm_api_config,
        )
