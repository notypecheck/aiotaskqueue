from datetime import datetime

import msgspec
from aiotaskqueue.broker.sql.sqlalchemy.models import PostgresBrokerTaskMixin
from aiotaskqueue.result.sql.sqlalchemy.models import PostgresResultTaskMixin
from sqlalchemy.orm import DeclarativeBase


class MsgspecModel(msgspec.Struct):
    a: int
    b: str
    now: datetime


class Base(DeclarativeBase): ...


class PostgresBrokerTask(PostgresBrokerTaskMixin, Base): ...


class PostgresResultTask(PostgresResultTaskMixin, Base): ...
