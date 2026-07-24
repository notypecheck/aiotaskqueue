import dataclasses
import itertools
from collections.abc import Callable, Sequence
from datetime import timedelta
from typing import Annotated, Any, Final

from typing_extensions import Doc

from aiotaskqueue.extensions import AnyExtension
from aiotaskqueue.extensions.builtin.logging import LoggingExtension
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
    shutdown_deadline: timedelta = timedelta(minutes=1)
    timeout_interval: Annotated[
        timedelta, Doc("Interval in which task is considered stuck/failed.")
    ] = timedelta(seconds=10)


def default_result_key(task_id: str) -> str:
    return f"aiotaskqueue:result:{task_id}"


@dataclasses.dataclass
class ResultBackendConfiguration:
    result_key: Callable[[str], str] = default_result_key
    result_ttl: timedelta = timedelta(days=1)


_DefaultExtension = Callable[[Sequence[AnyExtension]], AnyExtension | None]


def _logging_extension(extensions: Sequence[AnyExtension]) -> AnyExtension | None:
    return (
        None
        if any(isinstance(e, LoggingExtension) for e in extensions)
        else LoggingExtension()
    )


def _sentry_extension(extensions: Sequence[AnyExtension]) -> AnyExtension | None:
    try:
        from aiotaskqueue.extensions.builtin.sentry import (  # noqa: PLC0415
            SentryExtension,
        )
    except ImportError:
        return None
    return (
        None
        if any(isinstance(e, SentryExtension) for e in extensions)
        else SentryExtension()
    )


class Configuration:
    """Configuration is a semi-global object that defines behavior shared between different components, such as serialization, plugins and timeouts."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        task: Annotated[TaskConfiguration | None, Doc("task configuration")] = None,
        result: ResultBackendConfiguration | None = None,
        default_serialization_backend: Annotated[
            SerializationBackend[Any], Doc("default SerializationBackend")
        ],
        serialization_backends: Annotated[
            Sequence[SerializationBackend[Any]],
            Doc("list of serialization backends in order of priority"),
        ] = (),
        extensions: Sequence[AnyExtension] = (),
        default_extensions: Sequence[_DefaultExtension] = (
            _logging_extension,
            _sentry_extension,
        ),
    ) -> None:
        self.task: Final = task or TaskConfiguration()
        self.result: Final = result or ResultBackendConfiguration()
        self.default_serialization_backend: Final = default_serialization_backend
        self.serialization_backends: Final = {
            backend.id: backend
            for backend in itertools.chain(
                serialization_backends,
                (default_serialization_backend,),
            )
        }
        self.extensions: Sequence[AnyExtension] = [
            *extensions,
            *(
                ext
                for ext in (func(extensions) for func in default_extensions)
                if ext is not None
            ),
        ]
