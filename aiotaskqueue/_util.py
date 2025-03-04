from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiotaskqueue.router import TaskRouter
    from aiotaskqueue.tasks import TaskDefinition


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def extract_tasks(
    tasks: TaskRouter | Sequence[TaskDefinition[Any, Any]],
) -> Sequence[TaskDefinition[Any, Any]]:
    from aiotaskqueue.router import TaskRouter

    if isinstance(tasks, TaskRouter):
        return tuple(tasks.tasks.values())
    return tasks
