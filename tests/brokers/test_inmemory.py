import uuid

from aiotaskqueue._util import utc_now
from aiotaskqueue.broker.inmemory import InMemoryBroker
from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import BrokerTask


async def test_ctx(inmemory_broker: InMemoryBroker) -> None:
    async with inmemory_broker:
        pass


async def test_ack(inmemory_broker: InMemoryBroker) -> None:
    task = TaskRecord(
        id=str(uuid.uuid4()),
        enqueue_time=utc_now(),
        task_name="some-name",
        args=(),
        kwargs={},
    )
    async with inmemory_broker.ack_context(BrokerTask(task=task, meta=None)):
        pass
