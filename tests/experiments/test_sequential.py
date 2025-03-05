import asyncio
import random

from aiotaskqueue import Configuration, Publisher, TaskParams, TaskRouter, task
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.experimental.sequential import sequential, sequential_task
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.worker import AsyncWorker

from tests.utils import run_worker_until


async def test_sequential(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    redis_result_backend: ResultBackend,
) -> None:
    count = random.randint(3, 10)

    results = []
    finished = asyncio.Event()

    @task(TaskParams(name="test-task"))
    async def test_task(n: int) -> None:
        results.append(n)
        if len(results) == count:
            finished.set()

    worker = AsyncWorker(
        broker=broker,
        result_backend=redis_result_backend,
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
