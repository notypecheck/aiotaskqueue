import asyncio
import uuid
from datetime import datetime

import msgspec
import pytest
from aiotaskqueue import task
from aiotaskqueue.broker.redis import RedisClient
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.result.redis import RedisResultBackend
from aiotaskqueue.tasks import RunningTask

from tests.models import MsgspecModel


@pytest.fixture
def model(now: datetime) -> MsgspecModel:
    return MsgspecModel(a=42, b="str", now=now)


@task(name="some-task")
async def _task() -> MsgspecModel:
    raise NotImplementedError


async def test_set(
    redis: RedisClient,
    redis_result_backend: RedisResultBackend,
    model: MsgspecModel,
) -> None:
    task_id = str(uuid.uuid4())
    await redis_result_backend.set(task_id=task_id, value=model)

    stored = await redis.get(f"aiotaskqueue:result:{task_id}")
    assert stored == f"msgspec,{msgspec.json.encode(model).decode()}".encode()


async def test_wait_none(result_backend: ResultBackend) -> None:
    running_task = RunningTask(
        id=str(uuid.uuid4()),
        instance=_task(),
    )
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(1):
            await result_backend.wait(task=running_task)


async def test_wait_ok(result_backend: ResultBackend, model: MsgspecModel) -> None:
    running_task = RunningTask(
        id=str(uuid.uuid4()),
        instance=_task(),
    )
    await result_backend.set(task_id=running_task.id, value=model)

    result = await result_backend.wait(task=running_task)
    assert result == model
    assert result is not model
