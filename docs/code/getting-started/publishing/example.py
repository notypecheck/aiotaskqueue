import asyncio

from aiotaskqueue import Publisher, Configuration, task
from aiotaskqueue.broker.abc import Broker


@task(name="task")
async def notify_user(user_id: int, message: str) -> None:
    pass


async def main() -> None:
    broker: Broker
    confugration: Configuration

    publisher = Publisher(broker=broker, config=confugration)

    await publisher.enqueue(
        notify_user(
            user_id=42,
            message="Your notification!"
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
