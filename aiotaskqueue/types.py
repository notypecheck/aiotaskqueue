import enum
from typing import TYPE_CHECKING, Any, Generic, NewType, TypeVar

if TYPE_CHECKING:
    from aiotaskqueue.tasks import TaskDefinition

_T = TypeVar("_T")


class Some(Generic[_T]):
    def __init__(self, value: _T) -> None:
        self.value = value


CurrentTaskId = NewType("CurrentTaskId", str)
CurrentTaskDefinition = NewType("CurrentTaskDefinition", "TaskDefinition[Any, Any]")


class NoResult(enum.Enum):
    v = enum.auto()


NO_RESULT = NoResult.v
