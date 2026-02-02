from typing import Any, Generic, TypeVar

T = TypeVar("T")

class Runtime(Generic[T]):
	context: Any
