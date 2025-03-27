Aiotaskqueue is a type-safe and fast distributed queue alternative to celery, rq and arq.

## Example Usage

```python
import asyncio

from redis.asyncio import Redis

from aiotaskqueue import Configuration, Publisher, TaskRouter
from aiotaskqueue.broker.redis import RedisBroker, RedisBrokerConfig
from aiotaskqueue.serialization.msgspec import MsgSpecSerializer
from aiotaskqueue.serialization.pydantic import PydanticSerializer

router = TaskRouter()


@router.task(name="task-name")
async def task(a: int, b: str) -> None:
    print(a, b)


async def main() -> None:
    configuration = Configuration(
        serialization_backends=[PydanticSerializer()],
        default_serialization_backend=MsgSpecSerializer(),
    )

    redis = Redis(host="127.0.0.1")
    broker = RedisBroker(
        redis=redis,
        consumer_name="aiotaskqueue",
        broker_config=RedisBrokerConfig(xread_count=100),
    )
    publisher = Publisher(broker=broker, config=configuration)
    async with redis, broker:
        await publisher.enqueue(task(a=42, b="string"))


if __name__ == "__main__":
    asyncio.run(main())

```
