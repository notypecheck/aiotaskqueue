from aiotaskqueue import Publisher
from aiotaskqueue.broker.redis import RedisBroker, RedisBrokerConfig
from aiotaskqueue.config import Configuration
from aiotaskqueue.result.redis import RedisResultBackend
from aiotaskqueue.serialization.msgspec import MsgSpecSerializer
from aiotaskqueue.serialization.pydantic import PydanticSerializer
from redis.asyncio import Redis

configuration = Configuration(
    serialization_backends=[PydanticSerializer()],
    default_serialization_backend=MsgSpecSerializer(),
)
redis = Redis(host="127.0.0.1")

broker = RedisBroker(
    redis=redis,
    consumer_name="aiotaskqueue",
    broker_config=RedisBrokerConfig(xread_count=100, group_name="second"),
)
result_backend = RedisResultBackend(redis=redis, configuration=configuration)

publisher = Publisher(broker=broker, config=configuration)
