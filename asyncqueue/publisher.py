from asyncqueue._types import P, TResult
from asyncqueue.broker.abc import Broker
from asyncqueue.config import Configuration
from asyncqueue.serialization import serialize_task
from asyncqueue.tasks import RunningTask, TaskInstance


class Publisher:
    def __init__(self, broker: Broker, config: Configuration) -> None:
        self._broker = broker
        self._config = config

    async def enqueue(self, task: TaskInstance[P, TResult]) -> RunningTask[TResult]:
        record = serialize_task(
            task,
            default_backend=self._config.default_serialization_backend,
            serialization_backends=self._config.serialization_backends,
        )
        await self._broker.enqueue(record)
        return RunningTask(instance=task, id=record.id)
