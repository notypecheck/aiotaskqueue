from typing import Generic, TypeVar

_T = TypeVar("_T")


class Some(Generic[_T]):
    def __init__(self, value: _T) -> None:
        self.value = value
