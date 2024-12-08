from redis.asyncio import Redis

from asyncqueue.broker.abc import Broker
from asyncqueue.broker.redis import RedisBroker, RedisBrokerConfig
from asyncqueue.publisher import Configuration
from asyncqueue.result.abc import ResultBackend
from asyncqueue.result.redis import RedisResultBackend
from asyncqueue.serialization.msgspec import MsgSpecSerializer

configuration = Configuration(
    default_serialization_backend=MsgSpecSerializer,
)


def _redis() -> Redis:
    return Redis(host="127.0.0.1")


def create_broker() -> Broker:
    return RedisBroker(
        redis=_redis(),
        consumer_name="asyncqueue",
        config=RedisBrokerConfig(
            xread_count=1,
        ),
    )


def create_result_backend() -> ResultBackend:
    return RedisResultBackend(redis=_redis(), configuration=configuration)
