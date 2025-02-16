from datetime import datetime

import msgspec


class MsgspecModel(msgspec.Struct):
    a: int
    b: str
    now: datetime
