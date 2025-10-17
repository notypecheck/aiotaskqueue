import abc
from datetime import datetime

from aiotaskqueue.tasks import Marker


class Schedule(Marker, abc.ABC):
    @abc.abstractmethod
    def next_schedule(self, now: datetime) -> datetime: ...
