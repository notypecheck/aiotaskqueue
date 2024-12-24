from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, Generic, NewType

import msgspec

from asyncqueue._types import TResult
from asyncqueue._util import utc_now
from asyncqueue.tasks import TaskInstance

Deserializer = Callable[[bytes], TResult]
Serializer = Callable[[TResult], bytes]

SerializationBackendId = NewType("SerializationBackendId", str)


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class SerializationBackend(Generic[TResult]):
    id: SerializationBackendId
    instance_of: type[TResult]
    serialize: Serializer[TResult]
    deserialize: Deserializer[TResult]


def serialize(
    value: object,
    default_backend: SerializationBackend[object],
    backends: Mapping[SerializationBackendId, SerializationBackend[object]],
) -> tuple[SerializationBackendId, bytes]:
    for backend in backends.values():
        if isinstance(value, backend.instance_of):
            return backend.id, backend.serialize(value)

    return default_backend.id, default_backend.serialize(value)


class TaskRecord(msgspec.Struct, kw_only=True):
    id: str
    task_name: str
    requeue_count: int = 0
    enqueue_time: datetime
    args: list[tuple[SerializationBackendId, bytes]]
    kwargs: dict[str, tuple[SerializationBackendId, bytes]]


def serialize_task(
    task: TaskInstance[Any, Any],
    default_backend: SerializationBackend[object],
    serialization_backends: Mapping[
        SerializationBackendId,
        SerializationBackend[object],
    ],
) -> TaskRecord:
    args = [
        serialize(
            value,
            default_backend=default_backend,
            backends=serialization_backends,
        )
        for value in task.args
    ]
    kwargs = {
        key: serialize(
            value,
            default_backend=default_backend,
            backends=serialization_backends,
        )
        for key, value in task.kwargs.items()
    }
    return TaskRecord(
        id=str(uuid.uuid4()),
        task_name=task.task.params.name,
        enqueue_time=utc_now(),
        args=args,
        kwargs=kwargs,
    )


def deserialize_task(
    task: TaskRecord,
    serialization_backends: Mapping[
        SerializationBackendId,
        SerializationBackend[object],
    ],
) -> tuple[tuple[object, ...], dict[str, object]]:
    args = tuple(
        serialization_backends[backend_id].deserialize(value)
        for backend_id, value in task.args
    )
    kwargs = {
        key: serialization_backends[backend_id].deserialize(value)
        for key, (backend_id, value) in task.kwargs.items()
    }
    return args, kwargs
