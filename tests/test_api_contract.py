"""Test script to verify the API contract and refactoring status."""

from ebiose.backends.langgraph.llm_api import LangGraphLLMApi
from ebiose.core.llm_api import LLMApi
from ebiose.core.llm_api_factory import LLMApiFactory


def test_llm_api_refactoring() -> None:
    """Test that the refactoring is working correctly and types are preserved."""
    # Test 1: Factory should use LangGraphLLMApi by default
    api = LLMApiFactory.initialize(mode="local")
    assert api == LangGraphLLMApi, f"Expected LangGraphLLMApi, got {api}"

    # Test 2: LangGraphLLMApi should inherit from LLMApi
    assert issubclass(LangGraphLLMApi, LLMApi), (
        "LangGraphLLMApi should inherit from LLMApi"
    )

    # Test 3: LangGraphLLMApi should have the required methods
    assert hasattr(LangGraphLLMApi, "get_total_cost"), (
        "LangGraphLLMApi should have get_total_cost method"
    )
    assert hasattr(LangGraphLLMApi, "get_agent_cost"), (
        "LangGraphLLMApi should have get_agent_cost method"
    )
    assert hasattr(LangGraphLLMApi, "initialize"), (
        "LangGraphLLMApi should have initialize method"
    )

    # Test 4: LangGraphLLMApi should implement the abstract method
    assert hasattr(LangGraphLLMApi, "process_llm_call"), (
        "LangGraphLLMApi should have process_llm_call method"
    )
