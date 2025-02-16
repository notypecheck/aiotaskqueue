import contextlib
from collections.abc import AsyncIterator
from typing import Any

import anyio
import anyio.lowlevel
from asyncqueue.broker.abc import Broker
from asyncqueue.tasks import BrokerTask

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
