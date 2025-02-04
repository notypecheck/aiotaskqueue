import asyncio

from example._components import broker, publisher, result_backend
from example.tasks import Email, Person, send_email


async def main() -> None:
    async with broker:
        task = await publisher.enqueue(
            task=send_email(
                person=Person(id=42, name="Name"),
                email=Email(
                    text="Email text",
                    cc=["one@example.org", "second@example.org"],
                ),
            )
        )
        result = await result_backend.wait(task)
        print(result)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
