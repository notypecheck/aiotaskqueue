from asyncqueue.broker.inmemory import InMemoryBroker
from asyncqueue.config import Configuration
from asyncqueue.publisher import Publisher
from asyncqueue.router import task
from asyncqueue.serialization import deserialize_task
from asyncqueue.tasks import TaskParams

from tests.utils import capture_broker_messages


@task(TaskParams(name="test-task"))
async def target_task() -> None:
    pass


@task(TaskParams(name="task-with-params"))
async def task_with_params(a: int, b: str) -> None:
    pass


async def test_enqueue(broker: InMemoryBroker, publisher: Publisher) -> None:
    task_instance = target_task()

    async with capture_broker_messages(broker) as messages:
        await publisher.enqueue(task=task_instance)

    assert len(messages) == 1
    message = messages[0]
    assert message.task.task_name == target_task.params.name


async def test_enqueue_with_params(
    broker: InMemoryBroker,
    publisher: Publisher,
    configuration: Configuration,
) -> None:
    tasks = [task_with_params(a=i, b=str(i)) for i in range(10)]

    async with capture_broker_messages(broker) as messages:
        for task_to_publish in tasks:
            await publisher.enqueue(task_to_publish)

    for task_, message in zip(tasks, messages, strict=True):
        assert message.task.task_name == task_with_params.params.name
        args, kwargs = deserialize_task(
            message.task,
            serialization_backends=configuration.serialization_backends,
        )
        assert task_.args == args
        assert task_.kwargs == kwargs
