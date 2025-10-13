import asyncio
import dataclasses
from datetime import timedelta
from typing import Annotated, Any, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from typing_extensions import Doc

from aiotaskqueue._types import TResult
from aiotaskqueue.config import Configuration
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.result.sql.sqlalchemy.models import SqlalchemyResultTaskMixin
from aiotaskqueue.serialization import SerializationBackendId, serialize
from aiotaskqueue.tasks import RunningTask, TaskDefinition
from aiotaskqueue.types import Some


@dataclasses.dataclass(kw_only=True, slots=True)
class SqlalchemyResultBackendConfig:
    result_table: type[SqlalchemyResultTaskMixin]
    poll_interval: timedelta = timedelta(milliseconds=100)


class SqlalchemyPostgresResultBackend(ResultBackend):
    def __init__(
        self,
        engine: async_sessionmaker[AsyncSession] | AsyncEngine,
        backend_config: SqlalchemyResultBackendConfig,
        configuration: Configuration,
    ) -> None:
        self._session_maker = (
            async_sessionmaker(engine) if isinstance(engine, AsyncEngine) else engine
        )
        self._config = configuration
        self._backend_config = backend_config

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
        table = self._backend_config.result_table
        stmt = insert(table).values(
            {
                table.key: self._cache_key(task_id),
                table.value: f"{backend_id},{serialized_value}",
            }
        )
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[table.key],
            set_={
                table.value: stmt.excluded.value,
            },
        )
        async with self._session_maker.begin() as session:
            await session.execute(on_conflict_stmt)

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
        table = self._backend_config.result_table
        stmt = select(table).where(table.key == self._cache_key(task_id))
        async with self._session_maker.begin() as session:
            model = await session.scalar(stmt)

            if model is None:
                return None

            result = self._deserialize(
                model.value,
                return_type=definition.return_type,
            )
            return Some(cast("TResult", result))

    async def wait(
        self,
        task: RunningTask[TResult],
        *,
        poll_interval: float | None = None,
    ) -> TResult:
        poll_interval = (
            poll_interval or self._backend_config.poll_interval.total_seconds()
        )
        table = self._backend_config.result_table

        stmt = select(table).where(table.key == self._cache_key(task.id))
        while True:
            async with self._session_maker.begin() as session:
                model: SqlalchemyResultTaskMixin | None = None
                model = await session.scalar(stmt)
                if model is not None:
                    result = self._deserialize(
                        model.value,
                        return_type=task.instance.task.return_type,
                    )
                    return cast("TResult", result)
            await asyncio.sleep(poll_interval)

    def _deserialize(
        self,
        raw_value: str,
        return_type: type[Any],
    ) -> Any:  # noqa: ANN401
        backend_id, value = raw_value.split(",", maxsplit=1)
        return self._config.serialization_backends[
            SerializationBackendId(backend_id)
        ].deserialize(value=value, type=return_type)

    def _cache_key(self, task_id: str) -> str:
        return self._config.result.result_key(task_id)
