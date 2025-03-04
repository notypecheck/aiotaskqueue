import dataclasses
import itertools
from collections.abc import Sequence
from datetime import timedelta
from typing import Annotated, Any, Final

from typing_extensions import Doc

from aiotaskqueue.serialization import SerializationBackend


@dataclasses.dataclass
class TaskConfiguration:
    healthcheck_interval: Annotated[
        timedelta,
        Doc(
            "Interval in which worker should notify broker"
            "that task is being processed, if that's applicable."
        ),
    ] = timedelta(seconds=5)
    max_delivery_attempts: int = 3
    timeout_interval: Annotated[
        timedelta, Doc("Interval in which task is considered stuck/failed.")
    ] = timedelta(seconds=10)


class Configuration:
    """Configuration is a semi-global object that defines behavior shared between different components, such as serialization, plugins and timeouts."""

    def __init__(
        self,
        *,
        task: Annotated[TaskConfiguration | None, Doc("task configuration")] = None,
        default_serialization_backend: Annotated[
            SerializationBackend[Any], Doc("default SerializationBackend")
        ],
        serialization_backends: Annotated[
            Sequence[SerializationBackend[Any]] | None,
            Doc("list of serialization backends in order of priority"),
        ] = None,
    ) -> None:
        self.task = task or TaskConfiguration()
        self.default_serialization_backend: Final = default_serialization_backend
        self.serialization_backends: Final = {
            backend.id: backend
            for backend in itertools.chain(
                serialization_backends or (),
                (default_serialization_backend,),
            )
        }
