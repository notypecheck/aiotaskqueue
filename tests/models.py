from datetime import datetime

import msgspec
from aiotaskqueue.broker.sql.sqlalchemy.models import (
    SqlalchemyBrokerTaskMixin,
    SqlalchemyScheduledTaskMixin,
)
from aiotaskqueue.result.sql.sqlalchemy.models import SqlalchemyResultTaskMixin
from sqlalchemy.orm import DeclarativeBase


class MsgspecModel(msgspec.Struct):
    a: int
    b: str
    now: datetime


class Base(DeclarativeBase): ...


class SqlalchemyBrokerTask(SqlalchemyBrokerTaskMixin, Base): ...


class SqlalchemyScheduledTask(SqlalchemyScheduledTaskMixin, Base): ...


class SqlalchemyResultTask(SqlalchemyResultTaskMixin, Base): ...
