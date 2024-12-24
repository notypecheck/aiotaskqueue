import asyncio
import time

from example._components import broker, publisher, redis
from example.tasks import send_email


async def main() -> None:
    async with redis, broker:
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
