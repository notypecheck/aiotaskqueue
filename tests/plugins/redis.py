from collections.abc import AsyncIterator

import pytest
from aiotaskqueue.broker.redis import RedisClient
from testcontainers.redis import AsyncRedisContainer  # type: ignore[import-untyped]


@pytest.fixture(scope="session")
async def redis_container() -> AsyncIterator[RedisClient]:
    with AsyncRedisContainer(image="valkey/valkey:8.0.2-bookworm") as redis_container:
        yield redis_container


@pytest.fixture
async def redis(redis_container: AsyncRedisContainer) -> AsyncIterator[RedisClient]:
    async with await redis_container.get_async_client() as client:
        yield client
        await client.flushall()
