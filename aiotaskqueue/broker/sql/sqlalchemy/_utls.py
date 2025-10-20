import asyncio
from collections.abc import AsyncIterator, Sequence
from datetime import timedelta


async def pool(intervals: Sequence[timedelta]) -> AsyncIterator[None]:
    if intervals is None:
        raise ValueError

    for interval in intervals:
        yield
        await asyncio.sleep(interval.total_seconds())
