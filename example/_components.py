from asyncqueue import Publisher
from asyncqueue.broker.redis import RedisBroker, RedisBrokerConfig
from asyncqueue.config import Configuration
from asyncqueue.result.redis import RedisResultBackend
from asyncqueue.serialization.msgspec import MsgSpecSerializer
from asyncqueue.serialization.pydantic import PydanticSerializer
from redis.asyncio import Redis

configuration = Configuration(
    serialization_backends=[PydanticSerializer()],
    default_serialization_backend=MsgSpecSerializer(),
)
redis = Redis(host="127.0.0.1")

broker = RedisBroker(
    redis=redis,
    consumer_name="asyncqueue",
    broker_config=RedisBrokerConfig(xread_count=100, group_name="second"),
)
result_backend = RedisResultBackend(redis=redis, configuration=configuration)

publisher = Publisher(broker=broker, config=configuration)
