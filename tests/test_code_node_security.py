"""Test security constraints of CodeNode."""

import asyncio

import pytest

from ebiose.core.engines.graph_engine.nodes.code_node import CodeNode


def test_code_node_blocks_imports() -> None:
    """Test that CodeNode prevents importing modules."""
    node = CodeNode(id="test_node", name="test_code_execution")

    # State mocking a message with unsafe code
    unsafe_code = "import os; print(os.getcwd())"
    state = {
        "messages": [
            {"last_message": unsafe_code},
        ],
    }

    # Verify strict check
    assert node.is_safe_code(unsafe_code) is False

    # Verify execution fails
    with pytest.raises(ValueError, match="Unsafe code detected"):
        asyncio.run(node.call_node(state))


def test_code_node_safe_execution() -> None:
    """Test that safe code executes correctly."""
    node = CodeNode(id="test_node", name="test_code_execution")

    safe_code = "x = 1 + 1"
    expected_result = 2

    assert node.is_safe_code(safe_code) is True

    # We can test _execute_safe_code directly since it is synchronous and used by the async wrapper
    local_vars: dict[str, object] = {}
    node._execute_safe_code(safe_code, local_vars)  # noqa: SLF001
    assert local_vars["x"] == expected_result
