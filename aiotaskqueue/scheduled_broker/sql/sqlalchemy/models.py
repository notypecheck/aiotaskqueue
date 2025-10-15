import enum
from datetime import datetime
from typing import Annotated, Any

from sqlalchemy import JSON, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from aiotaskqueue.serialization import SerializationBackendId

datetime_tz = Annotated[datetime, mapped_column(DateTime(timezone=True))]


class ScheduledTaskStatus(enum.Enum):
    PENDING = enum.auto()
    SCHEDULED = enum.auto()


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


class SqlalchemyScheduledTaskMixin(_TaskPayloadMixin):
    __tablename__ = "aiotaskqueue_scheduled_task"
    __table_args__ = (
        Index(
            "ix_aiotaskqueue_scheduled_task_scheduled_at_id",
            "scheduled_at",
            "id",
            postgresql_where="status = 'PENDING'",
        ),
    )

    status: Mapped[ScheduledTaskStatus] = mapped_column(
        Enum(ScheduledTaskStatus, native_enum=False)
    )
    scheduled_at: Mapped[datetime_tz]
