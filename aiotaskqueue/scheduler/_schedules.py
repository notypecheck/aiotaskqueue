import dataclasses
from datetime import datetime, timedelta

from croniter import croniter

from aiotaskqueue.scheduler.abc import Schedule


@dataclasses.dataclass
class every(Schedule):  # noqa: N801
    timedelta: timedelta

    def next_schedule(self, now: datetime) -> datetime:
        return datetime.fromtimestamp(
            (now.timestamp() // self.timedelta.total_seconds() + 1)
            * self.timedelta.total_seconds(),
            tz=now.tzinfo,
        )


@dataclasses.dataclass
class crontab(Schedule):  # noqa: N801
    expression: str

    def __post_init__(self) -> None:
        if not croniter.is_valid(self.expression):
            msg = f"Invalid crontab expression: {self.expression}"
            raise ValueError(msg)

    def next_schedule(self, now: datetime) -> datetime:
        return croniter(self.expression, now).get_next(datetime)  # type: ignore[no-any-return]
