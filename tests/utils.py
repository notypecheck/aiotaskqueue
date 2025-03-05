import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

import anyio
import anyio.lowlevel
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.tasks import BrokerTask
from aiotaskqueue.worker import AsyncWorker

SOME_MAGIC_WAIT_TIME = 0.1


@contextlib.asynccontextmanager
async def capture_broker_messages(
    broker: Broker, count: int
) -> AsyncIterator[list[BrokerTask[Any]]]:
    messages: list[BrokerTask[Any]] = []

    async def capture() -> None:
        while len(messages) != count:
            messages.extend(await broker.read())

    async with anyio.create_task_group() as tg:
        tg.start_soon(capture)
        yield messages


@contextlib.asynccontextmanager
async def run_worker_until(
    worker: AsyncWorker, event: asyncio.Event
) -> AsyncIterator[None]:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(worker.run())
        yield
        await event.wait()
        worker.stop()
