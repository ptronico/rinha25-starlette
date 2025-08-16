import asyncio
from collections import deque


class AsyncDeque:
    def __init__(self):
        self._queue = deque()
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)

    async def push(self, item):
        async with self._lock:
            self._queue.append(item)
            self._not_empty.notify()

    async def re_push(self, item):
        async with self._lock:
            self._queue.appendleft(item)
            self._not_empty.notify()

    async def pop(self):
        async with self._not_empty:
            while not self._queue:
                await self._not_empty.wait()
            return self._queue.popleft()
