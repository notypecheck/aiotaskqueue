from collections.abc import AsyncIterator

import pytest
from aiotaskqueue import Configuration
from aiotaskqueue.broker.redis import RedisClient
from aiotaskqueue.result.redis import RedisResultBackend
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


@pytest.fixture
async def redis_result_backend(
    redis: RedisClient, configuration: Configuration
) -> RedisResultBackend:
    return RedisResultBackend(redis=redis, configuration=configuration)
