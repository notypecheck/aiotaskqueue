from typing import Any

import msgspec

from aiotaskqueue._util import INJECTED
from aiotaskqueue.config import Configuration
from aiotaskqueue.router import task
from aiotaskqueue.serialization import TaskRecord, deserialize_task, serialize_task
from aiotaskqueue.tasks import TaskInstance
from aiotaskqueue.worker import ExecutionContext


class Sequential(msgspec.Struct):
    tasks: tuple[TaskRecord, ...]


def sequential(
    *tasks: TaskInstance[Any, Any],
    configuration: Configuration,
) -> TaskInstance[[Sequential], None]:
    """Execute tasks in order."""
    records = tuple(
        serialize_task(
            task,
            default_backend=configuration.default_serialization_backend,
            serialization_backends=configuration.serialization_backends,
        )
        for task in tasks
    )
    return sequential_task(seq=Sequential(tasks=records))


@task(name="aiotaskqueue-sequential")
async def sequential_task(
    seq: Sequential,
    context: ExecutionContext = INJECTED,
) -> None:
    if not context.result_backend:  # pragma: no cover
        err_msg = "Result backend must be enabled in order to use sequential"
        raise ValueError(err_msg)

    for task_record in seq.tasks:
        task_definition = context.tasks.tasks[task_record.task_name]

        result = await context.result_backend.get(
            task_id=task_record.id,
            definition=task_definition,
        )
        if result is not None:
            continue

        args, kwargs = deserialize_task(
            task_definition=task_definition,
            task=task_record,
            serialization_backends=context.configuration.serialization_backends,
        )
        job = await context.publisher.enqueue(
            task_definition(*args, **kwargs), id=task_record.id
        )
        await context.result_backend.wait(job)
