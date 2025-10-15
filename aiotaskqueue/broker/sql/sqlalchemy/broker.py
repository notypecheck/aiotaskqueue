import asyncio
import contextlib
import dataclasses
from collections.abc import AsyncIterator, Sequence
from types import TracebackType
from typing import Annotated, Any, Self

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from typing_extensions import Doc

from aiotaskqueue._util import run_until_stopped, utc_now
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.broker.sql.sqlalchemy.models import (
    SqlalchemyBrokerTaskMixin,
    TaskStatus,
)
from aiotaskqueue.config import Configuration
from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import BrokerTask


@dataclasses.dataclass(kw_only=True, slots=True)
class SqlalchemyBrokerConfig:
    task_table: type[SqlalchemyBrokerTaskMixin]
    queue_name: str = "default"
    read_count: Annotated[
        int,
        Doc("Amount of entries to read from table at once"),
    ] = 1


@dataclasses.dataclass(kw_only=True, slots=True)
class SqlalchemyBrokerMeta:
    id: str


class SqlalchemyPostgresBroker(Broker):
    def __init__(
        self,
        engine: async_sessionmaker[AsyncSession] | AsyncEngine,
        broker_config: Annotated[
            SqlalchemyBrokerConfig, Doc("Sqlalchemy specific configuration")
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

    @contextlib.asynccontextmanager
    async def ack_context(self, task: BrokerTask[Any]) -> AsyncIterator[None]:
        try:
            yield
        except:
            await self.ack(task=task, status=TaskStatus.FAILED)
            raise
        else:
            await self.ack(task=task, status=TaskStatus.SUCCESS)

    async def enqueue(self, task: TaskRecord) -> None:
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
                table.status: TaskStatus.PENDING,
                table.queue_name: self._broker_config.queue_name,
                table.latest_healtcheck: now,
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
                table.queue_name: stmt.excluded.queue_name,
                table.latest_healtcheck: stmt.excluded.latest_healtcheck,
            },
        )
        async with self._session_maker.begin() as session:
            await session.execute(on_conflict_stmt)

    async def read(self) -> Sequence[BrokerTask[Any]]:
        table = self._broker_config.task_table

        pending_records_cte = (
            select(table.id)
            .where(
                table.queue_name == self._broker_config.queue_name,
                table.status == TaskStatus.PENDING,
            )
            .order_by(table.enqueue_time.asc(), table.id.asc())
            .limit(self._broker_config.read_count)
            .scalar_subquery()
        )
        stmt = (
            update(table)
            .values(status=TaskStatus.IN_PROCESS)
            .where(table.id.in_(pending_records_cte))
            .returning(table)
        )

        async with self._session_maker.begin() as session:
            records = sorted(
                (await session.scalars(stmt)).all(),
                key=lambda item: (item.enqueue_time, item.id),
            )
            return [
                BrokerTask(
                    meta=SqlalchemyBrokerMeta(id=record.id),
                    task=TaskRecord(
                        id=record.id,
                        task_name=record.task_name,
                        requeue_count=record.requeue_count,
                        enqueue_time=record.enqueue_time,
                        args=record.args,
                        kwargs=record.kwargs,
                        meta=record.meta,
                    ),
                )
                for record in records
            ]

    async def ack(
        self,
        task: BrokerTask[Any],
        *,
        status: TaskStatus = TaskStatus.SUCCESS,
    ) -> None:
        table = self._broker_config.task_table

        stmt = update(table).values(status=status).where(table.id == task.task.id)
        async with self._session_maker.begin() as session:
            await session.execute(stmt)

    async def run_worker_maintenance_tasks(
        self,
        stop: asyncio.Event,
        config: Configuration,
    ) -> None:
        await run_until_stopped(
            lambda: self._run_worker_maintenance_tasks(config=config),
            interval=config.task.healthcheck_interval,
            stop=stop,
        )

    async def _run_worker_maintenance_tasks(
        self,
        config: Configuration,
    ) -> None:
        table = self._broker_config.task_table
        unprocess_task_stmt = (
            update(table)
            .values(
                {
                    table.status: TaskStatus.PENDING,
                    table.requeue_count: table.requeue_count + 1,
                }
            )
            .where(
                table.queue_name == self._broker_config.queue_name,
                table.status == TaskStatus.IN_PROCESS,
                table.latest_healtcheck < (utc_now() - config.task.timeout_interval),
            )
        )
        async with self._session_maker.begin() as session:
            await session.execute(unprocess_task_stmt)

    async def tasks_healthcheck(self, *tasks: BrokerTask[Any]) -> None:
        table = self._broker_config.task_table

        stmt = (
            update(table)
            .values(latest_healtcheck=utc_now())
            .where(table.id.in_(task.meta.id for task in tasks))
        )
        async with self._session_maker.begin() as session:
            await session.execute(stmt)
