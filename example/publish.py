import asyncio
import time

from example._components import broker, publisher, redis
from example.tasks import Email, Person, send_email


async def main() -> None:
    async with redis, broker:
        t = time.perf_counter()
        await asyncio.gather(
            *[
                asyncio.create_task(
                    publisher.enqueue(
                        task=send_email(
                            person=Person(id=42, name="Name"),
                            email=Email(text="Email contents", cc=["different-email"]),
                        )
                    )
                )
                for i in range(1000)
            ]
        )
        print(time.perf_counter() - t)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
