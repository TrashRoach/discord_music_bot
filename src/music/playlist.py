import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from src.config import config
from src.music.track import Track


@dataclass(slots=True)
class Playlist:
    queue: deque[Track] = field(default_factory=deque)
    history: deque[Track] = field(default_factory=deque)
    loop: bool = False

    def add(self, track: Track) -> None:
        self.queue.append(track)

    def next(self) -> Optional[Track]:
        if self.loop:
            self.queue.appendleft(self.history[-1])
        if len(self.queue) == 0:
            return None
        if len(self.history) > config.MAX_HISTORY_LENGTH:
            self.history.pop()
        return self.queue[0]

    def prev(self, current: Optional[Track] = None) -> Optional[Track]:
        """
        TODO: revisit
        :param current:
        :return:
        """
        if current is None:
            # region TODO: Possibly unreachable state
            if len(self.history) == 0:
                return None
            # endregion
            self.queue.appendleft(self.history[0])
            return self.queue[0]

        # np_idx = self.history.index(current)
        self.queue.appendleft(self.history[1])

        if current is not None:
            self.queue.insert(1, current)

    def delete(self, pos: int) -> Track:
        track = self.queue[pos]
        del self.queue[pos]
        return track

    def shuffle(self):
        random.shuffle(self.queue)
