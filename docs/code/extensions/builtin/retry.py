from aiotaskqueue import task, Configuration
from aiotaskqueue.extensions.retry import RetryExtension, Retry
from aiotaskqueue.serialization.msgspec import MsgSpecSerializer


@task(
    name="name",
    markers=[Retry(max_retries=3)],  # (1)!
)
async def some_task() -> None:
    pass


configuration = Configuration(
    default_serialization_backend=MsgSpecSerializer(),
    extensions=[RetryExtension()],  # (2)!
)
