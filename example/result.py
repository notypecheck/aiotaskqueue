import asyncio
import uuid

from example._components import publisher, result_backend, broker
from example.tasks import send_email


async def main() -> None:
    async with broker:
        task = await publisher.enqueue(
            task=send_email(message=f"Email {uuid.uuid4()}", address="email-address")
        )
        result = await result_backend.wait(task)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
