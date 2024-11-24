import msgspec

from ._serialization import SerializationBackend, SerializationBackendId

MsgSpecSerializer = SerializationBackend(
    id=SerializationBackendId("msgspec"),
    instance_of=msgspec.Struct,
    serialize=msgspec.json.encode,
    deserialize=msgspec.json.decode,
)
