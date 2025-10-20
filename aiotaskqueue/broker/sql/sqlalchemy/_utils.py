import asyncio
from collections.abc import AsyncIterator, Sequence
from datetime import timedelta


async def pool(intervals: Sequence[timedelta]) -> AsyncIterator[None]:
    if not intervals:
        msg = "SqlalchemyBrokerConfig.read_block_times is empty"
        raise ValueError(msg)

    for interval in intervals:
        yield
        await asyncio.sleep(interval.total_seconds())

    while True:
        yield
        await asyncio.sleep(intervals[-1].total_seconds())
