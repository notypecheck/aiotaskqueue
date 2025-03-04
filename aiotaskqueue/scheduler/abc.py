from datetime import datetime
from typing import Protocol


class Schedule(Protocol):
    def next_schedule(self, now: datetime) -> datetime: ...
