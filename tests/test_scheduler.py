import asyncio
import contextlib
from datetime import UTC, datetime, timedelta

import pytest
import time_machine
from aiotaskqueue.broker.inmemory import InMemoryBroker
from aiotaskqueue.publisher import Publisher
from aiotaskqueue.router import task
from aiotaskqueue.scheduler import Scheduler, crontab, every

from tests.utils import capture_broker_messages

BASE_DATETIME = datetime(2000, 1, 1, tzinfo=UTC)


@task(name="every-task", schedule=every(timedelta(minutes=5)))
async def every_task() -> None:
    pass


@pytest.mark.parametrize(
    "datetime_",
    [
        BASE_DATETIME.replace(minute=1),
        BASE_DATETIME.replace(minute=6),
        BASE_DATETIME.replace(minute=22),
        BASE_DATETIME.replace(minute=47),
    ],
)
@pytest.mark.parametrize(
    "timedelta_",
    [
        timedelta(minutes=5),
        timedelta(hours=5),
        timedelta(days=5),
        timedelta(weeks=5),
    ],
)
async def test_every(datetime_: datetime, timedelta_: timedelta) -> None:
    every_schedule = every(timedelta_)

    assert every_schedule.next_schedule(datetime_) == datetime.fromtimestamp(
        (datetime_.timestamp() // timedelta_.total_seconds() + 1)
        * timedelta_.total_seconds(),
        tz=datetime_.tzinfo,
    )


async def test_invalid_crontab_expression() -> None:
    with pytest.raises(ValueError, match="Invalid crontab expression"):
        crontab("* * * *")


async def test_scheduler(
    broker: InMemoryBroker,
    publisher: Publisher,
) -> None:
    every_ = every(timedelta(minutes=5))
    attempts = 3

    timeout = asyncio.timeout(None)
    with time_machine.travel(BASE_DATETIME, tick=False) as frozen_time:
        async with capture_broker_messages(broker, count=attempts - 1) as messages:
            count = 0

            async def _sleep(_: float) -> None:
                nonlocal count
                nonlocal every_

                frozen_time.shift(every_.timedelta)
                count += 1
                if count == attempts:
                    timeout.reschedule(-1)

            scheduler = Scheduler(publisher=publisher, tasks=[every_task], sleep=_sleep)
            with contextlib.suppress(asyncio.TimeoutError):
                async with timeout:
                    await scheduler.run()

    datetime_ = BASE_DATETIME
    for message in messages:
        datetime_ = every_.next_schedule(datetime_)
        assert message.task.enqueue_time == datetime_
