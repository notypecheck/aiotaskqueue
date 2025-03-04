import asyncio
import logging

from aiotaskqueue.worker import AsyncWorker

from example._components import broker, configuration, redis, result_backend
from example.tasks import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with redis:
        worker = AsyncWorker(
            broker=broker,
            configuration=configuration,
            tasks=router,
            concurrency=20,
            result_backend=result_backend,
        )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
