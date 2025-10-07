from collections.abc import AsyncIterator, Mapping

import pytest
from _pytest.fixtures import SubRequest
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.broker.inmemory import InMemoryBroker
from aiotaskqueue.broker.redis import RedisBroker, RedisClient
from aiotaskqueue.broker.sql.sqlalchemy.broker import (
    SqlalchemyBrokerConfig,
    SqlalchemyPostgresBroker,
)
from aiotaskqueue.config import Configuration
from aiotaskqueue.publisher import Publisher
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.result.inmemory import InMemoryResultBackend
from aiotaskqueue.result.redis import RedisResultBackend
from aiotaskqueue.result.sql.sqlalchemy.backend import (
    SqlalchemyPostgresResultBackend,
    SqlalchemyResultBackendConfig,
)
from aiotaskqueue.serialization.msgspec import MsgSpecSerializer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.models import PostgresBrokerTask, PostgresResultTask


@pytest.fixture
def configuration() -> Configuration:
    return Configuration(
        default_serialization_backend=MsgSpecSerializer(),
    )


@pytest.fixture
def inmemory_broker() -> InMemoryBroker:
    return InMemoryBroker(max_buffer_size=100)


@pytest.fixture
async def redis_broker(redis: RedisClient) -> AsyncIterator[RedisBroker]:
    async with RedisBroker(
        redis=redis,
        consumer_name="pytest",
    ) as broker:
        yield broker


@pytest.fixture
async def sqlalchemy_broker(
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[SqlalchemyPostgresBroker]:
    async with SqlalchemyPostgresBroker(
        engine=sqlalchemy_session_maker,
        broker_config=SqlalchemyBrokerConfig(task_table=PostgresBrokerTask),
    ) as broker:
        yield broker


@pytest.fixture
async def broker_mapping(
    inmemory_broker: InMemoryBroker,
    redis_broker: RedisBroker,
    sqlalchemy_broker: SqlalchemyPostgresBroker,
) -> Mapping[str, Broker]:
    return {
        "inmemory_broker": inmemory_broker,
        "redis_broker": redis_broker,
        "sqlalchemy_broker": sqlalchemy_broker,
    }


@pytest.fixture(
    params=[
        "inmemory_broker",
        "redis_broker",
        "sqlalchemy_broker",
    ]
)
async def broker(
    broker_mapping: Mapping[str, Broker],
    request: SubRequest,
) -> Broker:
    return broker_mapping[request.param]


@pytest.fixture
def publisher(broker: Broker, configuration: Configuration) -> Publisher:
    return Publisher(broker=broker, config=configuration)


@pytest.fixture
def inmemory_result_backend(configuration: Configuration) -> InMemoryResultBackend:
    return InMemoryResultBackend(configuration=configuration)


@pytest.fixture
async def redis_result_backend(
    redis: RedisClient, configuration: Configuration
) -> RedisResultBackend:
    return RedisResultBackend(redis=redis, configuration=configuration)


@pytest.fixture
async def sqlalchemy_result_backend(
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
    configuration: Configuration,
) -> SqlalchemyPostgresResultBackend:
    return SqlalchemyPostgresResultBackend(
        engine=sqlalchemy_session_maker,
        backend_config=SqlalchemyResultBackendConfig(
            result_table=PostgresResultTask,
        ),
        configuration=configuration,
    )


@pytest.fixture
async def result_backend_mapping(
    inmemory_result_backend: InMemoryResultBackend,
    redis_result_backend: RedisResultBackend,
    sqlalchemy_result_backend: SqlalchemyPostgresResultBackend,
) -> Mapping[str, ResultBackend]:
    return {
        "inmemory_result_backend": inmemory_result_backend,
        "redis_result_backend": redis_result_backend,
        "sqlalchemy_result_backend": sqlalchemy_result_backend,
    }


@pytest.fixture(
    params=[
        "inmemory_result_backend",
        "redis_result_backend",
        "sqlalchemy_result_backend",
    ],
)
async def result_backend(
    result_backend_mapping: Mapping[str, ResultBackend],
    request: SubRequest,
) -> ResultBackend:
    return result_backend_mapping[request.param]
