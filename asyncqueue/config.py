import dataclasses
import itertools
from collections.abc import Sequence
from datetime import timedelta
from typing import Annotated, Any, Final

from typing_extensions import Doc

from asyncqueue.serialization import SerializationBackend


@dataclasses.dataclass
class TaskConfiguration:
    healthcheck_interval: Annotated[
        timedelta,
        Doc(
            "Interval in which worker should notify broker"
            "that task is being processed, if that's applicable."
        ),
    ] = timedelta(seconds=5)
    timeout_interval: Annotated[
        timedelta, Doc("Interval in which task is considered stuck/failed.")
    ] = timedelta(seconds=10)


class Configuration:
    def __init__(
        self,
        *,
        task: TaskConfiguration | None = None,
        default_serialization_backend: SerializationBackend[Any],
        serialization_backends: Sequence[SerializationBackend[Any]] | None = None,
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
