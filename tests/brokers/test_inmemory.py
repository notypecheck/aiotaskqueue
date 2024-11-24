import uuid

import pytest
from asyncqueue.broker.inmemory import InMemoryBroker
from asyncqueue.serialization import TaskRecord


@pytest.fixture
def broker() -> InMemoryBroker:
    return InMemoryBroker(max_buffer_size=100)


async def test_ctx(broker: InMemoryBroker) -> None:
    async with broker:
        pass


async def test_ack(broker: InMemoryBroker) -> None:
    task = TaskRecord(id=str(uuid.uuid4()), task_name="some-name", args=[], kwargs={})
    await broker.ack(task=task)
