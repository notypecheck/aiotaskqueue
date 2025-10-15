import asyncio
import contextlib
from datetime import UTC, datetime, timedelta

import time_machine
from aiotaskqueue._util import utc_now
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.config import Configuration
from aiotaskqueue.publisher import Publisher
from aiotaskqueue.router import task
from aiotaskqueue.scheduled_broker.abc import ScheduledBroker
from aiotaskqueue.scheduled_broker.scheduler import ScheduledTaskScheduler

from tests.utils import capture_broker_messages

BASE_DATETIME = datetime(2000, 1, 1, tzinfo=UTC)


@task(name="pow2-task")
async def pow2_task(a: int) -> int:
    return a**2


async def test_scheduled_task_push_to_queue(
    broker: Broker,
    scheduled_broker: ScheduledBroker,
    configuration: Configuration,
) -> None:
    after = timedelta(seconds=1)
    publisher = Publisher(
        broker=broker,
        scheduled_broker=scheduled_broker,
        config=configuration,
    )

    timeout = asyncio.timeout(None)

    async def _sleep(_: float) -> None:
        timeout.reschedule(-1)

    with time_machine.travel(BASE_DATETIME, tick=False) as frozen_time:
        task = await publisher.enqueue(pow2_task(2), after=after)
        frozen_time.shift(after)

        async with capture_broker_messages(broker, count=1) as messages:
            scheduler = ScheduledTaskScheduler(
                broker=broker,
                scheduled_broker=scheduled_broker,
                sleep=_sleep,
            )
            with contextlib.suppress(asyncio.TimeoutError):
                async with timeout:
                    await scheduler.run()

    assert len(messages) == 1

    message = messages[0]
    assert message.task.id == task.id


async def test_scheduled_task_not_duplicates(
    broker: Broker,
    scheduled_broker: ScheduledBroker,
    configuration: Configuration,
) -> None:
    publisher = Publisher(
        broker=broker,
        scheduled_broker=scheduled_broker,
        config=configuration,
    )

    with time_machine.travel(BASE_DATETIME, tick=False) as frozen_time:
        after = timedelta(seconds=1)
        await publisher.enqueue(pow2_task(2), after=after)

        for i in range(3):
            async with scheduled_broker.get_scheduled_tasks(utc_now()) as tasks:
                match i:
                    case 0:
                        assert len(tasks) == 0
                    case 1:
                        assert len(tasks) == 1
                    case 2:
                        assert len(tasks) == 0
                frozen_time.shift(after)


async def test_scheduled_task_raise_exception(
    broker: Broker,
    scheduled_broker: ScheduledBroker,
    configuration: Configuration,
) -> None:
    publisher = Publisher(
        broker=broker,
        scheduled_broker=scheduled_broker,
        config=configuration,
    )

    with time_machine.travel(BASE_DATETIME, tick=False) as frozen_time:
        after = timedelta(seconds=1)
        await publisher.enqueue(pow2_task(2), after=after)
        frozen_time.shift(after)

        with contextlib.suppress(ZeroDivisionError):
            async with scheduled_broker.get_scheduled_tasks(utc_now()) as tasks:
                assert tasks
                raise ZeroDivisionError

        async with scheduled_broker.get_scheduled_tasks(utc_now()) as tasks:
            assert tasks
