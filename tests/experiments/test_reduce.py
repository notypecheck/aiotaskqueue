import asyncio
import random
from typing import Any

import msgspec
import pytest
from aiotaskqueue import Configuration, Publisher, TaskRouter, task
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.experimental.reduce import reduce, reduce_task
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.tasks import RunningTask
from aiotaskqueue.worker import AsyncWorker, ExecutionContext
from pydantic import BaseModel

from tests.utils import run_worker_until


class SomePydanticModel(BaseModel):
    value: int


class SomeMsgSpecModel(msgspec.Struct):
    value: int


async def _wait_result(
    result_backend: ResultBackend,
    task: RunningTask[Any],
    finish_event: asyncio.Event,
) -> None:
    while True:
        result = await result_backend.get(task.id, task.instance)
        if result is not None:
            finish_event.set()
            return
        await asyncio.sleep(0.2)


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
        tasks=TaskRouter([reduce_task]),
    )


async def test_reduce_executed(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    result_backend: ResultBackend,
) -> None:
    count = random.randint(3, 6)

    results = []
    finished = asyncio.Event()

    @task(name="test-task")
    async def test_task(n: int) -> int:
        results.append(n)
        n += 1
        if len(results) == count:
            finished.set()
        return n

    worker = AsyncWorker(
        broker=broker,
        result_backend=result_backend,
        configuration=configuration,
        concurrency=10,
        tasks=TaskRouter([test_task, reduce_task]),
    )

    async with run_worker_until(worker, finished):
        reduce_task_instance = reduce(
            *[test_task for _ in range(count)],
            input=0,
            configuration=configuration,
        )
        running_task = await publisher.enqueue(
            reduce_task_instance,
        )
        await _wait_result(
            result_backend=result_backend,
            task=running_task,
            finish_event=finished,
        )

    assert results == list(range(count))


async def test_reduce_return_type(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    result_backend: ResultBackend,
) -> None:
    count = random.randint(3, 6)
    results = []
    finished = asyncio.Event()

    @task(name="test-task")
    async def test_task(n: int) -> int:
        results.append(n)
        return n + 1

    worker = AsyncWorker(
        broker=broker,
        result_backend=result_backend,
        configuration=configuration,
        concurrency=100,
        tasks=TaskRouter([test_task, reduce_task]),
    )

    async with run_worker_until(worker, finished):
        reduce_task_instance = reduce(
            *[test_task for _ in range(count)],
            input=0,
            configuration=configuration,
        )
        running_task = await publisher.enqueue(
            reduce_task_instance,
        )

        await _wait_result(
            result_backend=result_backend,
            task=running_task,
            finish_event=finished,
        )
        result = await result_backend.get(running_task.id, running_task.instance)

    assert result is not None
    assert result.value == count


async def test_reduce_map_type(
    broker: Broker,
    configuration: Configuration,
    publisher: Publisher,
    result_backend: ResultBackend,
) -> None:
    random_value = random.randint(3, 10)

    finished = asyncio.Event()

    @task(name="map-str-task")
    async def map_str_task(n: int) -> str:
        return str(n)

    @task(name="map-int-task")
    async def map_int_task(n: str) -> int:
        return int(n)

    @task(name="map-pydantic-task")
    async def map_pydantic_task(n: int) -> SomePydanticModel:
        return SomePydanticModel(value=n)

    @task(name="map-msgspec-task")
    async def map_msgspec_task(n: SomePydanticModel) -> SomeMsgSpecModel:
        finished.set()
        return SomeMsgSpecModel(value=n.value)

    worker = AsyncWorker(
        broker=broker,
        result_backend=result_backend,
        configuration=configuration,
        concurrency=10,
        tasks=TaskRouter(
            [
                map_str_task,
                map_int_task,
                map_pydantic_task,
                map_msgspec_task,
                reduce_task,
            ]
        ),
    )

    async with run_worker_until(worker, finished):
        running_task = await publisher.enqueue(
            reduce(
                map_str_task,
                map_int_task,
                map_pydantic_task,
                map_msgspec_task,
                input=random_value,
                configuration=configuration,
            ),
        )

        await _wait_result(
            result_backend=result_backend,
            task=running_task,
            finish_event=finished,
        )
        result = await result_backend.get(running_task.id, running_task.instance)

    assert result is not None
    assert isinstance(result.value, msgspec.Struct)
    assert result.value.value == random_value
