import asyncio
import contextlib

import pytest
from aiotaskqueue import Configuration, Publisher, TaskRouter
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.extensions.builtin import Retry, RetryExtension
from aiotaskqueue.worker import AsyncWorker

from tests.utils import run_worker_until

router = TaskRouter()


@pytest.mark.parametrize(
    "max_retries",
    [
        0,
        1,
        3,
    ],
)
async def test_should_retry(
    configuration: Configuration,
    broker: Broker,
    publisher: Publisher,
    max_retries: int,
) -> None:
    configuration.extensions = [RetryExtension()]
    worker = AsyncWorker(
        broker=broker,
        configuration=configuration,
        concurrency=10,
        tasks=router,
    )

    finished = asyncio.Event()

    execution_count = 0

    @router.task(
        name="retry-task",
        markers=[Retry(max_retries=max_retries)],
    )
    async def retry_task() -> None:
        nonlocal execution_count
        execution_count += 1
        if execution_count - 1 >= max_retries:
            finished.set()
        raise NotImplementedError

    async with run_worker_until(worker, finished):
        await publisher.enqueue(retry_task())

    assert execution_count - 1 == max_retries

    # Assert we don't have any tasks left in broker
    with contextlib.suppress(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            assert not await broker.read()
