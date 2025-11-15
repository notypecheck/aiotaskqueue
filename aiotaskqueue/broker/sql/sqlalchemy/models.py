import enum
from datetime import datetime
from typing import Annotated, Any

from sqlalchemy import JSON, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from aiotaskqueue.serialization import SerializationBackendId

datetime_tz = Annotated[datetime, mapped_column(DateTime(timezone=True))]


class TaskStatus(enum.Enum):
    PENDING = enum.auto()
    IN_PROCESS = enum.auto()
    SUCCESS = enum.auto()
    FAILED = enum.auto()


class _TaskPayloadMixin:
    id: Mapped[str] = mapped_column(primary_key=True)

    task_name: Mapped[str]
    requeue_count: Mapped[int] = mapped_column(insert_default=0, server_default="0")
    enqueue_time: Mapped[datetime_tz]

    args: Mapped[tuple[tuple[SerializationBackendId, str], ...]] = mapped_column(JSON())
    kwargs: Mapped[dict[str, tuple[SerializationBackendId, str]]] = mapped_column(
        JSON()
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSON())


class SqlalchemyBrokerTaskMixin(_TaskPayloadMixin):
    __tablename__ = "aiotaskqueue_task"
    __table_args__ = (
        Index(
            "ix_aiotaskqueue_task_queue_name_enqueue_time",
            "queue_name",
            "enqueue_time",
            "id",
            postgresql_where="status = 'PENDING'",
        ),
        Index(
            "ix_aiotaskqueue_task_queue_name_latest_healthcheck",
            "queue_name",
            "latest_healthcheck",
            postgresql_where="status = 'IN_PROCESS'",
        ),
    )

    queue_name: Mapped[str] = mapped_column()
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, native_enum=False))
    latest_healthcheck: Mapped[datetime_tz]
