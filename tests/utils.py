import asyncio
import contextlib
from collections.abc import AsyncIterator

import anyio
import anyio.lowlevel
from asyncqueue.broker.inmemory import InMemoryBroker
from asyncqueue.serialization import TaskRecord

SOME_MAGIC_WAIT_TIME = 0.1


@contextlib.asynccontextmanager
async def capture_broker_messages(
    broker: InMemoryBroker,
) -> AsyncIterator[list[TaskRecord]]:
    messages: list[TaskRecord] = []
    should_stop = asyncio.Event()

    async def capture() -> None:
        iterator = broker.listen()
        stop_task = asyncio.create_task(should_stop.wait())
        while True:
            next_coro = asyncio.create_task(anext(iterator))  # type: ignore[var-annotated, arg-type]
            await asyncio.wait(
                [next_coro, stop_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            if next_coro.done():
                messages.append(next_coro.result())

            if should_stop.is_set():
                return

    async with anyio.create_task_group() as tg:
        tg.start_soon(capture)
        yield messages
        await asyncio.sleep(0.1)
        should_stop.set()
