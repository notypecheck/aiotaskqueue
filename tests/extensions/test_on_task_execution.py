import asyncio
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from aiotaskqueue import Configuration, Publisher, TaskRouter
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.extensions.abc import OnTaskExecution
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.tasks import TaskDefinition
from aiotaskqueue.worker import AsyncWorker, ExecutionContext

from tests.utils import run_worker_until

T = TypeVar("T")


class _TextExtension(OnTaskExecution):
    def __init__(self, result_override: Any, done: asyncio.Event) -> None:  # noqa: ANN401
        self.result_override = result_override
        self.done = done

    async def on_task_execution(
        self,
        args: Any,  # noqa: ANN401
        kwargs: Any,  # noqa: ANN401
        definition: TaskDefinition[Any, T],  # noqa: ARG002
        context: ExecutionContext,
        call_next: Callable[
            [tuple[Any], dict[str, Any], ExecutionContext], Awaitable[T]
        ],
    ) -> T:
        await call_next(args, kwargs, context)
        self.done.set()
        return self.result_override  # type: ignore[no-any-return]


async def test_on_task_execution_extension(
    configuration: Configuration,
    broker: Broker,
    publisher: Publisher,
    result_backend: ResultBackend,
) -> None:
    done = asyncio.Event()

    router = TaskRouter()

    @router.task(name="test-task")
    async def test_task(arg: Any, *, kwarg: Any) -> str:  # noqa: ANN401
        assert arg == 1
        assert kwarg == 2  # noqa: PLR2004
        return str(uuid.uuid4())

    result_override = str(uuid.uuid4())
    configuration.extensions = [
        _TextExtension(result_override=result_override, done=done)
    ]

    worker = AsyncWorker(
        configuration=configuration,
        broker=broker,
        tasks=router,
        result_backend=result_backend,
        concurrency=10,
    )

    async with run_worker_until(worker, done):
        running_task = await publisher.enqueue(task=test_task(arg=1, kwarg=2))

    result = await result_backend.wait(running_task)
    assert result == result_override
