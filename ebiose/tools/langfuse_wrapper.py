"""Wrapper module for langfuse imports with fallbacks."""

from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")
F = Callable[P, R]


def _fallback_observe(*_args: object, **_kwargs: object) -> Callable[[F], F]:
    """Fallback observe decorator that does nothing."""
    del _args, _kwargs

    def decorator(func: F) -> F:
        return func

    return decorator


_observe: Callable[..., Callable[[F], F]] | None
try:
    from langfuse import observe as _observe
except ImportError:
    _observe = None

_CallbackHandler: type[object] | None
try:
    from langfuse.langchain import CallbackHandler as _CallbackHandler
except ImportError:
    _CallbackHandler = None


observe: Callable[..., Callable[[F], F]] = cast(
    "Callable[..., Callable[[F], F]]",
    _observe if _observe is not None else _fallback_observe,
)
CallbackHandler: type[object] | None = _CallbackHandler

__all__ = ["CallbackHandler", "observe"]
