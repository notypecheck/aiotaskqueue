import asyncio
from datetime import timedelta
from typing import Annotated, Any, cast

from typing_extensions import Doc

from aiotaskqueue._types import TResult
from aiotaskqueue.config import Configuration
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.serialization import SerializationBackendId, serialize
from aiotaskqueue.tasks import RunningTask, TaskDefinition
from aiotaskqueue.types import Some


class InMemoryResultBackend(ResultBackend):
    def __init__(
        self,
        configuration: Configuration,
        poll_interval: timedelta = timedelta(milliseconds=100),
    ) -> None:
        self._storage: dict[str, tuple[str, str]] = {}
        self._config = configuration
        self._poll_interval = poll_interval.total_seconds()

    async def set(
        self,
        task_id: Annotated[
            str,
            Doc("Task id"),
        ],
        value: Annotated[
            TResult,
            Doc(
                "Result value, supported by any of serialization backends in your config."
            ),
        ],
    ) -> None:
        backend_id, serialized_value = serialize(
            value=value,
            default_backend=self._config.default_serialization_backend,
            backends=self._config.serialization_backends,
        )
        self._storage[task_id] = backend_id, serialized_value

    async def get(
        self,
        task_id: Annotated[
            str,
            Doc("Task id"),
        ],
        definition: Annotated[
            TaskDefinition[Any, TResult],
            Doc("Task definition for the task you're trying to retrieve."),
        ],
    ) -> Some[TResult] | None:
        raw = self._storage.get(task_id)

        if raw is None:
            return None

        backend_id, value = raw
        result = self._deserialize(
            backend_id=backend_id,
            value=value,
            return_type=definition.return_type,
        )
        return Some(cast("TResult", result))

    async def wait(self, task: RunningTask[TResult]) -> TResult:
        while True:
            raw = self._storage.get(task.id)
            if raw is not None:
                backend_id, value = raw
                result = self._deserialize(
                    backend_id=backend_id,
                    value=value,
                    return_type=task.instance.task.return_type,
                )
                return cast("TResult", result)
            await asyncio.sleep(self._poll_interval)

    def _deserialize(
        self,
        *,
        backend_id: str,
        value: str,
        return_type: type[Any],
    ) -> Any:  # noqa: ANN401
        return self._config.serialization_backends[
            SerializationBackendId(backend_id)
        ].deserialize(value=value, type=return_type)
