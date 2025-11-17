import asyncio
import uuid
from collections.abc import Sequence
from datetime import timedelta
from typing import Any, TypeVar, overload

import msgspec

from aiotaskqueue._util import INJECTED
from aiotaskqueue.config import Configuration
from aiotaskqueue.router import task
from aiotaskqueue.serialization import SerializationBackendId, serialize
from aiotaskqueue.tasks import TaskDefinition, TaskInstance
from aiotaskqueue.types import NO_RESULT, CurrentTaskId, NoResult
from aiotaskqueue.worker import ExecutionContext

_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")
_D = TypeVar("_D")
_E = TypeVar("_E")
_F = TypeVar("_F")
_G = TypeVar("_G")


class ReduceTaskState(msgspec.Struct):
    tasks: Sequence[tuple[str, str]]

    serialized_value: tuple[SerializationBackendId, str]

    sleep: timedelta
    result_task_id: str | None = None
    current_task_index: int = 0


@overload
def reduce(
    __t1: TaskDefinition[[_A], _B],
    __t2: TaskDefinition[[_B], _C],
    /,
    *,
    input: _A,
    configuration: Configuration,
    sleep: timedelta = timedelta(seconds=0.1),
) -> TaskInstance[[_A], _C]: ...


@overload
def reduce(
    __t1: TaskDefinition[[_A], _B],
    __t2: TaskDefinition[[_B], _C],
    __t3: TaskDefinition[[_C], _D],
    /,
    *,
    input: _A,
    configuration: Configuration,
    sleep: timedelta = timedelta(seconds=0.1),
) -> TaskInstance[[_A], _D]: ...


@overload
def reduce(
    __t1: TaskDefinition[[_A], _B],
    __t2: TaskDefinition[[_B], _C],
    __t3: TaskDefinition[[_C], _D],
    __t4: TaskDefinition[[_D], _E],
    /,
    *,
    input: _A,
    configuration: Configuration,
    sleep: timedelta = timedelta(seconds=0.1),
) -> TaskInstance[[_A], _E]: ...


@overload
def reduce(
    __t1: TaskDefinition[[_A], _B],
    __t2: TaskDefinition[[_B], _C],
    __t3: TaskDefinition[[_C], _D],
    __t4: TaskDefinition[[_D], _E],
    __t5: TaskDefinition[[_E], _F],
    /,
    *,
    input: _A,
    configuration: Configuration,
    sleep: timedelta = timedelta(seconds=0.1),
) -> TaskInstance[[_A], _F]: ...


@overload
def reduce(
    __t1: TaskDefinition[[_A], _B],
    __t2: TaskDefinition[[_B], _C],
    __t3: TaskDefinition[[_C], _D],
    __t4: TaskDefinition[[_D], _E],
    __t5: TaskDefinition[[_E], _F],
    __t6: TaskDefinition[[_F], _G],
    /,
    *,
    input: _A,
    configuration: Configuration,
    sleep: timedelta = timedelta(seconds=0.1),
) -> TaskInstance[[_A], _G]: ...


def reduce(
    *tasks: TaskDefinition[Any, Any],
    input: Any,  # noqa: A002
    configuration: Configuration,
    sleep: timedelta = timedelta(seconds=0.1),
) -> TaskInstance[[Any], Any]:
    last_task = tasks[-1]
    input_parameter = serialize(
        input,
        default_backend=configuration.default_serialization_backend,
        backends=configuration.serialization_backends,
    )
    return reduce_task(
        state=ReduceTaskState(
            tasks=[(task.name, str(uuid.uuid4())) for task in tasks],
            serialized_value=input_parameter,
            sleep=sleep,
        )
    ).with_return_type(last_task.return_type)


@task("aiotaskqueue-reduce")
async def reduce_task(
    state: ReduceTaskState,
    current_id: CurrentTaskId = INJECTED,
    context: ExecutionContext = INJECTED,
) -> NoResult:
    if not context.result_backend:
        err_msg = "Result backend must be enabled in order to use reduce"
        raise ValueError(err_msg)
    if not state.tasks:
        return NO_RESULT

    if state.current_task_index == 0:
        task_name, _ = state.tasks[state.current_task_index]
        task_definition = context.tasks.tasks[task_name]
        backend_id, serialized_value = state.serialized_value
        args = context.configuration.serialization_backends[backend_id].deserialize(
            serialized_value,
            task_definition.arg_types[0],
        )
    else:
        previous_task_name, previous_task_id = state.tasks[state.current_task_index - 1]
        previous_task_definition = context.tasks.tasks[previous_task_name]

        while True:
            result = await context.result_backend.get(
                previous_task_id,
                previous_task_definition,
            )
            if result is not None:
                args = result.value
                break
            await asyncio.sleep(state.sleep.total_seconds())

        if state.current_task_index >= len(state.tasks) and not isinstance(
            args, NoResult
        ):
            await context.result_backend.set(
                task_id=state.result_task_id,  # type: ignore[arg-type]
                value=args,
            )
            return NO_RESULT

    task_name, task_id = state.tasks[state.current_task_index]
    task_definition = context.tasks.tasks[task_name]

    await context.publisher.enqueue(
        task_definition(args),
        id=task_id,
    )

    await context.publisher.enqueue(
        reduce_task(
            state=ReduceTaskState(
                tasks=state.tasks,
                serialized_value=state.serialized_value,
                sleep=state.sleep,
                current_task_index=state.current_task_index + 1,
                result_task_id=current_id
                if state.current_task_index == 0
                else state.result_task_id,
            ),
        ),
    )

    return NO_RESULT
