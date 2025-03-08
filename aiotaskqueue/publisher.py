from aiotaskqueue._types import P, TResult
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.config import Configuration
from aiotaskqueue.serialization import serialize_task
from aiotaskqueue.tasks import RunningTask, TaskInstance


class Publisher:
    def __init__(
        self,
        broker: Broker,
        config: Configuration,
    ) -> None:
        self._broker = broker
        self._config = config

    async def enqueue(
        self,
        task: TaskInstance[P, TResult],
        *,
        id: str | None = None,  # noqa: A002
    ) -> RunningTask[TResult]:
        record = serialize_task(
            task,
            default_backend=self._config.default_serialization_backend,
            serialization_backends=self._config.serialization_backends,
            id=id,
        )
        await self._broker.enqueue(record)
        return RunningTask(instance=task, id=record.id)
