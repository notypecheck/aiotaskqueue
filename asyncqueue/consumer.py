import asyncio

import anyio.abc
from anyio.streams.memory import MemoryObjectReceiveStream

from asyncqueue.broker.abc import Broker
from asyncqueue.publisher import Configuration
from asyncqueue.result.abc import ResultBackend
from asyncqueue.router import TaskRouter
from asyncqueue.serialization import TaskRecord, deserialize_task


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

    async def run(self) -> None:
        send, recv = anyio.create_memory_object_stream[TaskRecord]()

        async with self._broker, self._tg as tg, send:
            tg.start_soon(self._broker.run_worker_maintenance_tasks, self._stop)

            for _ in range(self._concurrency):
                tg.start_soon(self._worker, recv.clone())

            async for message in self._broker.listen():
                await send.send(message)

    async def _worker(self, recv: MemoryObjectReceiveStream[TaskRecord]) -> None:
        async for task in recv:
            task_definition = self._tasks.tasks[task.task_name]
            args, kwargs = deserialize_task(
                task, self._configuration.serialization_backends
            )
            result = await task_definition.func(*args, **kwargs)
            await self._broker.ack(task)
            if self._result_backend:
                await self._result_backend.set(task_id=task.id, value=result)
