import msgspec
from msgspec import Struct

from aiotaskqueue._types import TResult

from ._serialization import SerializationBackend, SerializationBackendId


class MsgSpecSerializer(SerializationBackend[Struct]):
    id = SerializationBackendId("msgspec")

    def serializable(self, value: Struct) -> bool:
        return isinstance(value, msgspec.Struct)

    def serialize(self, value: Struct) -> bytes:
        return msgspec.json.encode(value)

    def deserialize(self, value: bytes, type: type[TResult]) -> TResult:
        return msgspec.json.decode(value, type=type)
