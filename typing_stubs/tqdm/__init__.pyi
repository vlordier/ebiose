from collections.abc import Iterable, Iterator
from typing import Any, TypeVar

T = TypeVar("T")

def tqdm(iterable: Iterable[T], *args: Any, **kwargs: Any) -> Iterator[T]: ...
