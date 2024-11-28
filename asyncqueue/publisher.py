import itertools
from collections.abc import Sequence
from typing import Any

from asyncqueue._types import P, TResult
from asyncqueue.broker.abc import Broker
from asyncqueue.serialization import SerializationBackend, serialize_task
from asyncqueue.task import RunningTask, TaskInstance


class Configuration:
    def __init__(
        self,
        *,
        default_serialization_backend: SerializationBackend[Any],
        serialization_backends: Sequence[SerializationBackend[Any]] | None = None,
    ) -> None:
        self.default_serialization_backend = default_serialization_backend
        self.serialization_backends = {
            backend.id: backend
            for backend in itertools.chain(
                serialization_backends or (),
                (default_serialization_backend,),
            )
        }


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
