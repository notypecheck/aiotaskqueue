import asyncio
import time

from asyncqueue.publisher import Publisher
from example._components import create_broker, configuration
from example.tasks import send_email


async def main() -> None:
    async with create_broker() as broker:
        publisher = Publisher(broker=broker, config=configuration)
        t = time.perf_counter()
        await asyncio.gather(
            *[
                asyncio.create_task(
                    publisher.enqueue(
                        task=send_email(
                            address=f"user{i}@example.com", message=f"Message {i}"
                        )
                    )
                )
                for i in range(1000)
            ]
        )
        print(time.perf_counter() - t)


if __name__ == "__main__":
    asyncio.run(main())
