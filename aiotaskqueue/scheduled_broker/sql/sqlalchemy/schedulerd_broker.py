import contextlib
import dataclasses
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from types import TracebackType
from typing import Annotated, Self

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from typing_extensions import Doc

from aiotaskqueue._util import utc_now
from aiotaskqueue.scheduled_broker.abc import ScheduledBroker
from aiotaskqueue.scheduled_broker.sql.sqlalchemy.models import (
    ScheduledTaskStatus,
    SqlalchemyScheduledTaskMixin,
)
from aiotaskqueue.serialization import TaskRecord


@dataclasses.dataclass(kw_only=True, slots=True)
class SqlalchemyScheduledBrokerConfig:
    task_table: type[SqlalchemyScheduledTaskMixin]
    read_count: Annotated[
        int,
        Doc("Amount of entries to read from table at once"),
    ] = 10


class SqlalchemyPostgresScheduledBroker(ScheduledBroker):
    def __init__(
        self,
        engine: async_sessionmaker[AsyncSession] | AsyncEngine,
        broker_config: Annotated[
            SqlalchemyScheduledBrokerConfig, Doc("Sqlalchemy specific configuration")
        ],
    ) -> None:
        self._session_maker = (
            async_sessionmaker(engine) if isinstance(engine, AsyncEngine) else engine
        )
        self._broker_config = broker_config

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def schedule(
        self,
        task: TaskRecord,
        schedule_at: datetime,
    ) -> None:
        table = self._broker_config.task_table
        now = utc_now()
        stmt = insert(table).values(
            {
                table.id: task.id,
                table.task_name: task.task_name,
                table.requeue_count: task.requeue_count,
                table.enqueue_time: now,
                table.args: task.args,
                table.kwargs: task.kwargs,
                table.meta: task.meta,
                table.status: ScheduledTaskStatus.PENDING,
                table.scheduled_at: schedule_at,
            }
        )
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[table.id],
            set_={
                table.task_name: stmt.excluded.task_name,
                table.requeue_count: stmt.excluded.requeue_count,
                table.enqueue_time: stmt.excluded.enqueue_time,
                table.args: stmt.excluded.args,
                table.kwargs: stmt.excluded.kwargs,
                table.meta: stmt.excluded.meta,
                table.status: stmt.excluded.status,
                table.scheduled_at: stmt.excluded.scheduled_at,
            },
        )
        async with self._session_maker.begin() as session:
            await session.execute(on_conflict_stmt)

    @contextlib.asynccontextmanager
    async def get_scheduled_tasks(
        self,
        now: datetime,
    ) -> AsyncIterator[Sequence[TaskRecord]]:
        table = self._broker_config.task_table
        pending_records_cte = (
            select(table.id)
            .where(
                table.status == ScheduledTaskStatus.PENDING,
                table.scheduled_at <= now,
            )
            .order_by(table.scheduled_at.asc(), table.id.asc())
            .limit(self._broker_config.read_count)
            .scalar_subquery()
        )
        stmt = (
            update(table)
            .values(status=ScheduledTaskStatus.SCHEDULED)
            .where(table.id.in_(pending_records_cte))
            .returning(table)
        )
        async with self._session_maker.begin() as session:
            records = sorted(
                (await session.scalars(stmt)).all(),
                key=lambda item: (item.scheduled_at, item.id),
            )
            yield [
                TaskRecord(
                    id=record.id,
                    task_name=record.task_name,
                    requeue_count=record.requeue_count,
                    enqueue_time=record.scheduled_at,
                    args=record.args,
                    kwargs=record.kwargs,
                    meta=record.meta,
                )
                for record in records
            ]
