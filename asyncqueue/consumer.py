import anyio.abc
from anyio.streams.memory import MemoryObjectReceiveStream

from asyncqueue.broker.abc import Broker
from asyncqueue.publisher import Configuration
from asyncqueue.router import TaskRouter
from asyncqueue.serialization import TaskRecord, deserialize_task


class AsyncWorker:
    def __init__(
        self,
        broker: Broker,
        tasks: TaskRouter,
        config: Configuration,
        concurrency: int,
    ) -> None:
        self._broker = broker
        self._tasks = tasks
        self._config = config
        self._concurrency = concurrency
        self._tg = anyio.create_task_group()

    async def run(self) -> None:
        send, recv = anyio.create_memory_object_stream[TaskRecord](max_buffer_size=10)

        async with self._broker, self._tg as tg, send:
            for _ in range(self._concurrency):
                tg.start_soon(self._worker, recv.clone())

            async for message in self._broker.listen():
                await send.send(message)

    async def _worker(self, recv: MemoryObjectReceiveStream[TaskRecord]) -> None:
        async for task in recv:
            task_id = task.task_name
            task_definition = self._tasks.tasks[task_id]
            args, kwargs = deserialize_task(task, self._config.serialization_backends)
            await task_definition.func(*args, **kwargs)
            await self._broker.ack(task)
