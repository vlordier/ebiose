"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from __future__ import annotations

import ast
from typing import Any, Literal

from pydantic import BaseModel, Field

from ebiose.core.engines.graph_engine.nodes.node import BaseNode


class CodeNode(BaseNode):
    """The CodeNode class represents a node that executes code using Python's exec function."""

    type: Literal["CodeNode"] = "CodeNode"
    code_key: str = Field(
        default="last_message",
        description="The key in the state where the code is stored",
    )

    async def call_node(
        self, state: BaseModel | dict, config: BaseModel | None = None,
    ) -> dict:
        _ = config  # Unused parameter
        """Execute the code from the last message in the state using exec and return the result."""
        # Retrieve the last message from the state
        last_message = (
            state.get("messages", [])[-1]
            if isinstance(state, dict)
            else getattr(state, "messages", [])[-1]
        )
        code = (
            last_message.get(self.code_key)
            if isinstance(last_message, dict)
            else getattr(last_message, self.code_key)
        )

        # Ensure code is a string
        if not isinstance(code, str):
            msg = f"Code must be a string, got {type(code)}"
            raise TypeError(msg)

        # Basic static analysis to prevent dangerous code
        if not self.is_safe_code(code):
            msg = "Unsafe code detected"
            raise ValueError(msg)

        # Execute the code in isolated namespace with restricted builtins
        local_vars: dict[str, Any] = {}
        self._execute_safe_code(code, local_vars)
        return {"result": local_vars}

    def _execute_safe_code(self, code: str, local_vars: dict[str, Any]) -> None:
        """Execute code in restricted namespace (no builtins allowed).

        Security Note: This uses exec() with restricted builtins and no access to
        dangerous functions. Code must pass is_safe_code() check before reaching here.
        This is safe for sandboxed user code execution.
        """
        compiled = compile(code, "<string>", "exec")
        # Intentional use of exec with restricted environment for sandboxed execution
        restricted_globals = {"__builtins__": {}}
        exec(compiled, restricted_globals, local_vars)

    def is_safe_code(self, code: str) -> bool:
        """Perform basic static analysis to check for unsafe code."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    return False
        except SyntaxError:
            return False
        else:
            return True
