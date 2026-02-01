from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

def observe(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...
