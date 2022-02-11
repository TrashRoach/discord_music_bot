import asyncio


class Timer:
    def __init__(self, callback):
        self._callback = callback
        self._task = asyncio.create_task(self._timer())

    async def _timer(self):
        await asyncio.sleep(60 * 5)
        await self._callback()

    def cancel(self):
        self._task.cancel()
