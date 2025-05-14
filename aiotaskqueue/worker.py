import asyncio
import contextlib
import dataclasses
import functools
import inspect
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any

import anyio.abc
from anyio.streams.memory import MemoryObjectReceiveStream

from aiotaskqueue._util import ShutdownManager, TaskManager
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.config import Configuration
from aiotaskqueue.extensions import OnTaskCompletion, OnTaskException
from aiotaskqueue.extensions.abc import OnTaskExecution
from aiotaskqueue.extensions.middleware import MiddlewareStack
from aiotaskqueue.publisher import Publisher
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.router import TaskRouter
from aiotaskqueue.serialization import TaskRecord, deserialize_task
from aiotaskqueue.tasks import BrokerTask, TaskDefinition


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class ExecutionContext:
    configuration: Configuration
    broker: Broker
    publisher: Publisher
    result_backend: ResultBackend | None
    tasks: TaskRouter

    state: dict[str, Any] = dataclasses.field(default_factory=dict)


@functools.lru_cache
def _dependencies_to_inject(
    function: Callable[..., Any],
    types: Sequence[type[object]],
) -> Mapping[str, type[object]]:
    signature = inspect.signature(function)
    result = {}
    for key, parameter in signature.parameters.items():
        if parameter.annotation in types:
            result[key] = parameter.annotation
    return result


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
        self._publisher = Publisher(broker=broker, config=configuration)
        self._result_backend = result_backend
        self._tasks = tasks
        self._configuration = configuration
        self._concurrency = concurrency

        self._ext_on_task_exception = [
            ext for ext in configuration.extensions if isinstance(ext, OnTaskException)
        ]
        self._ext_on_task_completion = [
            ext for ext in configuration.extensions if isinstance(ext, OnTaskCompletion)
        ]
        self._ext_on_task_execution = [
            ext for ext in configuration.extensions if isinstance(ext, OnTaskExecution)
        ]

        self._active_tasks: dict[str, BrokerTask[Any]] = {}
        self._shutdown_manager = ShutdownManager()
        self._task_manager = TaskManager()

    def _create_execution_context(self) -> ExecutionContext:
        return ExecutionContext(
            configuration=self._configuration,
            broker=self._broker,
            publisher=self._publisher,
            result_backend=self._result_backend,
            tasks=self._tasks,
        )

    async def run(self) -> None:
        send, recv = anyio.create_memory_object_stream[BrokerTask[object]]()

        async with (
            self._broker,
            asyncio.TaskGroup() as tg,
            self._shutdown_tasks(),
            send,
        ):
            self._task_manager.add(
                tg.create_task(
                    self._broker.run_worker_maintenance_tasks(
                        stop=self._shutdown_manager.event,
                        config=self._configuration,
                    ),
                )
            )
            self._task_manager.add(tg.create_task(self._claim_pending_tasks()))
            self._task_manager.add(
                *(
                    tg.create_task(self._worker(recv=recv.clone()))
                    for _ in range(self._concurrency)
                )
            )

            stop_task = asyncio.create_task(self._shutdown_manager.event.wait())
            while True:
                read_task = asyncio.create_task(self._broker.read())
                await asyncio.wait(
                    {stop_task, read_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if self._shutdown_manager.event.is_set():
                    read_task.cancel()
                    break
                for message in read_task.result():
                    if (
                        message.task.requeue_count
                        >= self._configuration.task.max_delivery_attempts
                    ):
                        await self._broker.ack(message)

                    await send.send(message)

    @contextlib.asynccontextmanager
    async def _shutdown_tasks(self) -> AsyncIterator[None]:
        try:
            yield
        finally:
            try:
                async with asyncio.timeout(
                    self._configuration.task.shutdown_deadline.total_seconds(),
                ):
                    await self._task_manager.wait_for_completion()
            except TimeoutError:
                await self._task_manager.cancel()

    def stop(self) -> None:
        self._shutdown_manager.shutdown()

    async def _worker(self, recv: MemoryObjectReceiveStream[BrokerTask[Any]]) -> None:
        async for broker_task in recv:
            self._active_tasks[broker_task.task.id] = broker_task
            task = broker_task.task
            task_definition = self._tasks.tasks[task.task_name]

            execution_context = self._create_execution_context()

            try:
                async with self._broker.ack_context(task=broker_task):
                    result = await self._call_task_fn(
                        task=task,
                        task_definition=task_definition,
                        execution_context=execution_context,
                    )
            except Exception as e:  # noqa: BLE001
                for on_task_exception in self._ext_on_task_exception:
                    await on_task_exception.on_task_exception(
                        task=task,
                        definition=task_definition,
                        context=execution_context,
                        exception=e,
                    )
                continue
            finally:
                self._active_tasks.pop(broker_task.task.id, None)

            if self._result_backend:
                await self._result_backend.set(task_id=task.id, value=result)

            for on_task_completion in self._ext_on_task_completion:
                await on_task_completion.on_task_completion(
                    task=task,
                    definition=task_definition,
                    context=execution_context,
                    result=result,
                )

    async def _call_task_fn(
        self,
        task: TaskRecord,
        task_definition: TaskDefinition[Any, Any],
        execution_context: ExecutionContext,
    ) -> object:
        args, kwargs = deserialize_task(
            task_definition=task_definition,
            task=task,
            serialization_backends=self._configuration.serialization_backends,
        )
        for key, value in _dependencies_to_inject(
            task_definition.func,
            types=(ExecutionContext,),
        ).items():
            if value is ExecutionContext:
                obj = execution_context
            else:
                raise ValueError
            kwargs.setdefault(key, obj)

        middleware_stack = MiddlewareStack(
            middlewares=self._ext_on_task_execution,
            task_definition=task_definition,
        )
        return await middleware_stack.call(
            args,
            kwargs,
            context=execution_context,
        )

    async def _claim_pending_tasks(self) -> None:
        stop_task = asyncio.create_task(self._shutdown_manager.event.wait())
        while True:
            if self._active_tasks:
                await self._broker.tasks_healthcheck(*self._active_tasks.values())

            sleep_task = asyncio.create_task(
                asyncio.sleep(
                    self._configuration.task.healthcheck_interval.total_seconds()
                )
            )
            await asyncio.wait(
                {stop_task, sleep_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if self._shutdown_manager.event.is_set():
                return
