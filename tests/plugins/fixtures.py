import pytest
from aiotaskqueue.broker.abc import Broker
from aiotaskqueue.broker.inmemory import InMemoryBroker
from aiotaskqueue.config import Configuration
from aiotaskqueue.publisher import Publisher
from aiotaskqueue.serialization.msgspec import MsgSpecSerializer


@pytest.fixture
def configuration() -> Configuration:
    return Configuration(
        default_serialization_backend=MsgSpecSerializer(),
    )


@pytest.fixture
def broker() -> InMemoryBroker:
    return InMemoryBroker(max_buffer_size=16)


@pytest.fixture
def publisher(broker: Broker, configuration: Configuration) -> Publisher:
    return Publisher(broker=broker, config=configuration)
