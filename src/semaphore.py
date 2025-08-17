import asyncio


class ElasticSemaphore(asyncio.Semaphore):
    async def set_value(self, new_value: int):
        if new_value == self._value:
            return
        if new_value > self._value:
            delta: int = new_value - self._value
            for _ in range(delta):
                self.release()
        if new_value < self._value:
            delta: int = self._value - new_value
            for _ in range(delta):
                await self.acquire()
