import asyncio
import uuid

from redis.asyncio import Redis

from asyncqueue.publisher import Publisher
from asyncqueue.result.redis import RedisResultBackend
from example._components import create_broker, configuration
from example.tasks import send_email


async def main() -> None:
    async with create_broker() as broker:
        publisher = Publisher(broker=broker, config=configuration)
        result_backend = RedisResultBackend(
            redis=Redis(host="127.0.0.1"), configuration=configuration
        )

        task = await publisher.enqueue(
            task=send_email(message=f"Email {uuid.uuid4()}", address="email-address")
        )

        result = await result_backend.wait(task)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
