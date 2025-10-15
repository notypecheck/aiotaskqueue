import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from aiotaskqueue._util import ShutdownManager, utc_now
from aiotaskqueue.broker.abc import Broker, ScheduledBroker


class ScheduledTaskScheduler:
    def __init__(
        self,
        *,
        broker: Broker,
        scheduled_broker: ScheduledBroker,
        sleep: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        self._broker = broker
        self._scheduled_broker = scheduled_broker
        self._sleep = sleep

        self._shutdown_manager = ShutdownManager()

    async def run(self) -> None:
        stop_task = asyncio.create_task(self._shutdown_manager.event.wait())
        while True:
            async with self._scheduled_broker.get_scheduled_tasks(
                now=utc_now(),
            ) as tasks:
                await self._broker.enqueue_batch(tasks)

            sleep_task = asyncio.create_task(self._sleep(1))
            await asyncio.wait(
                {stop_task, sleep_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if self._shutdown_manager.event.is_set():
                return

    def stop(self) -> None:
        self._shutdown_manager.shutdown()
