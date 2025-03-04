from typing import Any

import pytest
from aiotaskqueue import TaskRouter
from aiotaskqueue._util import extract_tasks
from aiotaskqueue.tasks import TaskDefinition

from tests.tasks import noop_task, task_with_params

_router = TaskRouter([noop_task, task_with_params])


@pytest.mark.parametrize(
    ("tasks", "expected"),
    [
        ([noop_task, task_with_params], [noop_task, task_with_params]),
        (_router, tuple(_router.tasks.values())),
    ],
)
def test_extract_tasks(
    tasks: list[TaskDefinition[Any, object]] | TaskRouter,
    expected: list[TaskDefinition[Any, object]],
) -> None:
    assert extract_tasks(tasks) == expected
