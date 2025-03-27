import asyncio
import random
from typing import Any

import pytest
from aiotaskqueue import Configuration, Publisher, TaskRouter, task
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.worker import AsyncWorker, ExecutionContext

from tests.utils import run_worker_until


async def test_execute_func(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
) -> None:
    increment_count = random.randint(1, 10)

    counter = 0
    target_reached = asyncio.Event()

    @task(name="test-task")
    async def test_task() -> None:
        nonlocal counter
        counter += 1
        if counter == increment_count:
            target_reached.set()

    worker = AsyncWorker(
        broker=broker,
        configuration=configuration,
        concurrency=2,
        tasks=TaskRouter([test_task]),
    )

    async with run_worker_until(worker, target_reached):
        assert counter == 0

        for _ in range(increment_count):
            await publisher.enqueue(test_task())

    assert counter == increment_count


@pytest.mark.parametrize("dependency_cls", [ExecutionContext])
async def test_inject_dependencies(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    dependency_cls: type[object],
) -> None:
    finished = asyncio.Event()

    @task(name="test-task")
    async def test_task(dep: dependency_cls = Any) -> None:  # type: ignore[valid-type]
        assert isinstance(dep, dependency_cls)
        finished.set()

    worker = AsyncWorker(
        broker=broker,
        configuration=configuration,
        concurrency=2,
        tasks=TaskRouter([test_task]),
    )

    async with run_worker_until(worker, finished):
        await publisher.enqueue(test_task())
