from collections.abc import Iterable
from typing import Any, TypeVar

T = TypeVar("T")

class SortedList(list[T]):
    def __init__(self, iterable: Iterable[T] | None = None, *args: Any, **kwargs: Any) -> None: ...
    def add(self, value: T) -> None: ...
