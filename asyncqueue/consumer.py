import asyncio
from typing import Any

import anyio.abc
from anyio.streams.memory import MemoryObjectReceiveStream

from asyncqueue.broker.abc import Broker
from asyncqueue.config import Configuration
from asyncqueue.result.abc import ResultBackend
from asyncqueue.router import TaskRouter
from asyncqueue.serialization import deserialize_task
from asyncqueue.tasks import BrokerTask


class AsyncWorker:
    def __init__(
        self,
        broker: Broker,
        *,
        result_backend: ResultBackend | None = None,
        tasks: TaskRouter,
        configuration: Configuration,
        concurrency: int,
    ) -> None:
        self._broker = broker
        self._result_backend = result_backend
        self._tasks = tasks
        self._configuration = configuration
        self._concurrency = concurrency
        self._tg = anyio.create_task_group()
        self._stop = asyncio.Event()

        self._active_tasks: dict[str, BrokerTask[Any]] = {}

    async def run(self) -> None:
        send, recv = anyio.create_memory_object_stream[BrokerTask[object]]()

        async with self._broker, self._tg as tg, send:
            tg.start_soon(
                self._broker.run_worker_maintenance_tasks,
                self._stop,
                self._configuration,
            )
            tg.start_soon(self._claim_pending_tasks, self._stop)

            for _ in range(self._concurrency):
                tg.start_soon(self._worker, recv.clone())

            async for message in self._broker.listen():
                await send.send(message)

    async def _worker(self, recv: MemoryObjectReceiveStream[BrokerTask[Any]]) -> None:
        async for broker_task in recv:
            self._active_tasks[broker_task.task.id] = broker_task
            task = broker_task.task

            async with self._broker.ack_context(broker_task):
                task_definition = self._tasks.tasks[task.task_name]
                args, kwargs = deserialize_task(
                    task, self._configuration.serialization_backends
                )
                result = await task_definition.func(*args, **kwargs)

            self._active_tasks.pop(broker_task.task.id, None)

            if self._result_backend:
                await self._result_backend.set(task_id=task.id, value=result)

    async def _claim_pending_tasks(self, stop: asyncio.Event) -> None:
        closes = asyncio.create_task(stop.wait())
        while True:
            if self._active_tasks:
                await self._broker.tasks_healthcheck(*self._active_tasks.values())

            sleep_task = asyncio.create_task(
                asyncio.sleep(
                    self._configuration.task.healthcheck_interval.total_seconds()
                )
            )
            await asyncio.wait(
                {closes, sleep_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if stop.is_set():
                return
