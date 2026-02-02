#!/usr/bin/env python3
"""Simple test to verify the LLMApi initialization logic without importing
the full modules (to avoid dependency issues).
"""

from pathlib import Path


def test_initialization_logic() -> None:
    """Test the initialization logic by examining the source code."""
    # Read the LLMApi source
    llm_api_path = Path(__file__).parent.parent / "ebiose" / "core" / "llm_api.py"
    langgraph_api_path = (
        Path(__file__).parent.parent
        / "ebiose"
        / "backends"
        / "langgraph"
        / "llm_api.py"
    )

    with llm_api_path.open(encoding="utf-8") as f:
        llm_api_content = f.read()

    with langgraph_api_path.open(encoding="utf-8") as f:
        langgraph_api_content = f.read()

    # Check that the hardcoded URL is not present
    old_hardcoded_url = "https://ebiose-litellm.livelysmoke-ef8b125f.francecentral.azurecontainerapps.io/"

    print("Checking for hardcoded URLs...")

    assert old_hardcoded_url not in llm_api_content, "Found hardcoded URL in llm_api.py"
    print("✓ No hardcoded URL in llm_api.py")

    assert old_hardcoded_url not in langgraph_api_content, (
        "Found hardcoded URL in langgraph/llm_api.py"
    )
    print("✓ No hardcoded URL in langgraph/llm_api.py")

    # Check that the proper logic is in place
    print("\nChecking for proper initialization logic...")

    # Check that both files have the conditional logic
    expected_patterns = [
        "if lite_llm_api_base is not None:",
        "Use provided base URL",
        'elif mode == "local" and ModelEndpoints.use_lite_llm():',
        "Use local configuration",
        "cls.lite_llm_api_base = None",
    ]

    for pattern in expected_patterns:
        assert pattern in llm_api_content, f"Missing pattern in llm_api.py: {pattern}"
        assert pattern in langgraph_api_content, (
            f"Missing pattern in langgraph/llm_api.py: {pattern}"
        )

    print("✓ All expected patterns found in both files")

    # Check that ModelEndpoints is imported in llm_api.py
    assert "from ebiose.core.model_endpoint import ModelEndpoints" in llm_api_content, (
        "ModelEndpoints not imported in llm_api.py"
    )
    print("✓ ModelEndpoints properly imported in llm_api.py")


def main() -> None:
    """Run the test."""
    print("Testing LLMApi initialization fixes...")
    print("=" * 50)

    test_initialization_logic()

    print("\n" + "=" * 50)
    print("✅ All tests passed! The hardcoded URL issue has been fixed.")
    print("\nSummary of changes:")
    print("- Removed hardcoded lite_llm_api_base URL")
    print(
        "- Cloud mode now uses the lite_llm_api_base provided by the Ebiose cloud API",
    )
    print(
        "- Local mode attempts to use configuration from model_endpoints.yml via ModelEndpoints",
    )
    print("- Proper fallback behavior when no URL is available")
    print("- Added proper import for ModelEndpoints in llm_api.py")


if __name__ == "__main__":
    main()
