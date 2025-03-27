from __future__ import annotations

from pydantic import BaseModel

from ._serialization import SerializationBackend, SerializationBackendId


class PydanticSerializer(SerializationBackend[BaseModel]):
    id = SerializationBackendId("pydantic")

    def serializable(self, value: BaseModel) -> bool:
        return isinstance(value, BaseModel)

    def serialize(self, value: BaseModel) -> str:
        return value.model_dump_json()

    def deserialize(self, value: str, type: type[BaseModel]) -> BaseModel:
        return type.model_validate_json(value)
