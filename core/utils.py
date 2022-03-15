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


def get_similarity_coefficient(s1, s2) -> float:
    """
    Tanimoto similarity index.
    """
    a, b, c = len(s1), len(s2), 0.0
    for symbol in s1:
        if symbol in s2:
            c += 1
    return c / (a + b - c)
