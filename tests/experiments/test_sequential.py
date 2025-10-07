import asyncio
import random

import pytest
from aiotaskqueue import Configuration, Publisher, TaskRouter, task
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.experimental.sequential import Sequential, sequential, sequential_task
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.worker import AsyncWorker, ExecutionContext

from tests.utils import run_worker_until


@pytest.fixture
def execution_context(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    result_backend: ResultBackend,
) -> ExecutionContext:
    return ExecutionContext(
        configuration=configuration,
        broker=broker,
        publisher=publisher,
        result_backend=result_backend,
        tasks=TaskRouter([sequential_task]),
    )


async def test_sequential(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    result_backend: ResultBackend,
) -> None:
    count = random.randint(3, 10)

    results = []
    finished = asyncio.Event()

    @task(name="test-task")
    async def test_task(n: int) -> None:
        results.append(n)
        if len(results) == count:
            finished.set()

    worker = AsyncWorker(
        broker=broker,
        result_backend=result_backend,
        configuration=configuration,
        concurrency=10,
        tasks=TaskRouter([test_task, sequential_task]),
    )

    async with run_worker_until(worker, finished):
        await publisher.enqueue(
            sequential(
                *[test_task(i) for i in range(count)],
                configuration=configuration,
            )
        )

    assert results == list(range(count))


@pytest.mark.parametrize(
    ("total_tasks", "random_tasks_to_mark_as_completed"),
    [(3, 1), (3, 3), (3, 0), (10, 5)],
)
async def test_should_skip_executed_tasks(
    broker: Broker,
    execution_context: ExecutionContext,
    total_tasks: int,
    random_tasks_to_mark_as_completed: int,
) -> None:
    assert execution_context.result_backend
    finished = asyncio.Event()

    if total_tasks == random_tasks_to_mark_as_completed:
        finished.set()

    results = []

    @execution_context.tasks.task(name="test-task")
    async def test_task(n: int) -> None:
        results.append(n)
        if len(results) == total_tasks - random_tasks_to_mark_as_completed:
            finished.set()

    tasks = [test_task(i) for i in range(total_tasks)]

    sequential_task = sequential(*tasks, configuration=execution_context.configuration)
    record: Sequential = sequential_task.kwargs["seq"]  # type: ignore[assignment]
    for random_task in random.sample(
        record.tasks,
        k=random_tasks_to_mark_as_completed,
    ):
        await execution_context.result_backend.set(random_task.id, value=None)
    expected_result = [
        value
        for record, instance, value in zip(
            record.tasks, tasks, range(total_tasks), strict=True
        )
        if await execution_context.result_backend.get(
            record.id, definition=instance.task
        )
        is None
    ]

    worker = AsyncWorker(
        broker=broker,
        result_backend=execution_context.result_backend,
        configuration=execution_context.configuration,
        concurrency=10,
        tasks=execution_context.tasks,
    )
    async with run_worker_until(worker, finished):
        await execution_context.publisher.enqueue(sequential_task)

    assert results == expected_result
