import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime

import pytest
import time_machine
from asyncqueue._util import utc_now
from asyncqueue.broker.redis import RedisBroker, RedisBrokerConfig, RedisClient
from asyncqueue.serialization import deserialize_task, serialize_task
from asyncqueue.serialization.msgspec import MsgSpecSerializer
from testcontainers.redis import AsyncRedisContainer  # type: ignore[import-untyped]

from tests.tasks import noop_task, task_with_params
from tests.utils import capture_broker_messages


@pytest.fixture(scope="session")
async def redis_container() -> AsyncIterator[RedisClient]:
    with AsyncRedisContainer(image="valkey/valkey:8.0.1-bookworm") as redis_container:
        yield redis_container


@pytest.fixture
async def redis(redis_container: AsyncRedisContainer) -> AsyncIterator[RedisClient]:
    async with await redis_container.get_async_client() as client:
        yield client
        await client.flushall()


@pytest.fixture
async def redis_broker(redis: RedisClient) -> AsyncIterator[RedisBroker]:
    async with RedisBroker(
        redis=redis,
        consumer_name="pytest",
    ) as broker:
        yield broker


async def test_broker_init(redis: RedisClient) -> None:
    stream_name = "stream"

    assert not await redis.exists(stream_name)
    broker_config = RedisBrokerConfig(
        stream_name=stream_name, group_name=str(uuid.uuid4())
    )
    async with RedisBroker(
        redis=redis,
        consumer_name="pytest",
        broker_config=broker_config,
    ):
        pass

    assert await redis.exists(stream_name)
    groups = await redis.xinfo_groups(name=broker_config.stream_name)  # type: ignore[no-untyped-call]
    assert len(groups) == 1
    assert groups[0]["name"] == broker_config.group_name.encode()

    # Test entering context twice is ok
    async with RedisBroker(
        redis=redis,
        consumer_name="pytest",
        broker_config=broker_config,
    ):
        pass


async def test_enter_twice_is_ok(redis: RedisClient) -> None:
    broker = RedisBroker(redis=redis, consumer_name="pytest")
    async with broker, broker:
        pass


async def test_enqueue(redis_broker: RedisBroker, now: datetime) -> None:
    serializer = MsgSpecSerializer()

    tasks = [task_with_params(i, b=str(i)) for i in range(10)]
    now = utc_now()
    with time_machine.travel(now, tick=False):
        async with capture_broker_messages(redis_broker, count=len(tasks)) as messages:
            for task_instance in tasks:
                task_record = serialize_task(
                    task=task_instance,
                    default_backend=serializer,
                    serialization_backends={serializer.id: serializer},
                )
                await redis_broker.enqueue(task=task_record)

    for broker_task, task_instance in zip(messages, tasks, strict=True):
        args, kwargs = deserialize_task(
            task_definition=task_instance.task,
            task=broker_task.task,
            serialization_backends={serializer.id: serializer},
        )
        assert args
        assert kwargs
        assert args == task_instance.args
        assert kwargs == task_instance.kwargs

        assert broker_task.task.enqueue_time == now
        assert broker_task.task.task_name == task_instance.task.params.name


@pytest.mark.parametrize("count", [1, 5, 10])
async def test_listen(redis_broker: RedisBroker, count: int) -> None:
    serializer = MsgSpecSerializer()

    expected_tasks = [
        serialize_task(
            task=noop_task(),
            default_backend=serializer,
            serialization_backends={serializer.id: serializer},
        )
        for _ in range(count)
    ]

    async def add_test_tasks() -> None:
        for task_record in expected_tasks:
            await redis_broker.enqueue(task_record)

    result = []
    async with asyncio.TaskGroup() as tg:
        tg.create_task(add_test_tasks())
        async for task in redis_broker.listen():
            result.append(task)
            if len(result) == count:
                break

    assert [r.task for r in result] == expected_tasks
