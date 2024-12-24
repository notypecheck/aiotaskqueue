from redis.asyncio import Redis

from asyncqueue import Publisher
from asyncqueue.broker.redis import RedisBroker
from asyncqueue.config import Configuration
from asyncqueue.consumer import AsyncWorker
from asyncqueue.result.redis import RedisResultBackend
from asyncqueue.serialization.msgspec import MsgSpecSerializer
from example.tasks import router

configuration = Configuration(
    default_serialization_backend=MsgSpecSerializer,
)
redis = Redis(host="127.0.0.1")

broker = RedisBroker(redis=redis, consumer_name="asyncqueue")
result_backend = RedisResultBackend(redis=redis, configuration=configuration)

publisher = Publisher(broker=broker, config=configuration)
