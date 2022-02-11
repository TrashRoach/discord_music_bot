import itertools
import random
from collections import deque

import discord


class Playlist:
    __slots__ = ('play_queue', 'play_history', 'loop')

    def __init__(self):
        self.play_queue = deque()
        self.play_history = deque()
        self.loop = False

    def __len__(self):
        return len(self.play_queue)

    def add(self, track):
        self.play_queue.append(track)

    def next(self):
        if self.loop:
            self.play_queue.appendleft(self.play_history[-1])

        if len(self.play_queue) == 0:
            return None

        return self.play_queue[0]

    def delete(self, pos):
        track = self.play_queue[pos]
        del self.play_queue[pos]
        return track

    def prev(self, current_track):
        if current_track is None:
            self.play_queue.appendleft(self.play_history[-1])
            return self.play_queue[0]

        np_index = self.play_history.index(current_track)
        self.play_queue.appendleft(self.play_history[np_index - 1])

        if current_track is not None:
            self.play_queue.insert(1, current_track)

    def shuffle(self):
        random.shuffle(self.play_queue)

    def clear(self):
        self.play_queue.clear()
        # self.play_history.clear()

    def create_embed(self, title: str, page_num: int) -> discord.Embed or None:
        songs_per_page = 10

        if title == 'Recently played':
            playlist = self.play_history
            playlist_len = len(playlist)
            pages_max = playlist_len // songs_per_page + (playlist_len % songs_per_page > 0)

            # Prioritize the last page
            if page_num is None or page_num >= pages_max:
                page_num = pages_max - 1
            elif page_num <= 0:
                page_num = 0
            else:
                page_num = page_num - 1
        else:
            playlist = self.play_queue
            playlist_len = len(playlist)
            pages_max = playlist_len // songs_per_page + (playlist_len % songs_per_page > 0)

            # Prioritize the first page
            if page_num is None or page_num <= 0:
                page_num = 0
            elif pages_max < page_num:
                page_num = pages_max - 1
            else:
                page_num = page_num - 1

        if playlist_len == 0:
            return None

        queue = list(itertools.islice(playlist, page_num * 10, 10 + page_num * 10))

        fmt = '\n'.join(f'{i}.  {track}' for i, track in enumerate(queue, start=page_num * 10 + 1))
        if pages_max > 1:
            title += f' page {page_num + 1}/{pages_max}'
        return discord.Embed(title=title, description=fmt)
