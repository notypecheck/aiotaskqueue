import pytest
from asyncqueue.broker.abc import Broker
from asyncqueue.broker.inmemory import InMemoryBroker
from asyncqueue.publisher import Configuration, Publisher
from asyncqueue.serialization.msgspec import MsgSpecSerializer


@pytest.fixture(scope="session")
def configuration() -> Configuration:
    return Configuration(default_serialization_backend=MsgSpecSerializer)


@pytest.fixture
def broker() -> InMemoryBroker:
    return InMemoryBroker(max_buffer_size=16)


@pytest.fixture
def publisher(broker: Broker, configuration: Configuration) -> Publisher:
    return Publisher(broker=broker, config=configuration)
