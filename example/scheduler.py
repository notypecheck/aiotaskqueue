import asyncio

from aiotaskqueue.publisher import Publisher
from aiotaskqueue.scheduler import Scheduler

from example._components import broker, configuration
from example.tasks import router


async def main() -> None:
    async with broker:
        scheduler = Scheduler(
            publisher=Publisher(broker=broker, config=configuration),
            tasks=router,
        )
        await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())
