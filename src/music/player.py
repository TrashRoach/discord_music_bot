import asyncio
import concurrent.futures
import datetime
import itertools
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import discord
from discord.ext import commands

from src.config import config
from src.music.playlist import Playlist
from src.music.track import Track
from src.sources import youtube


@dataclass
class Player:
    bot: commands.Bot
    guild: discord.Guild
    channel: discord.TextChannel = None
    current_track: Optional[Track] = None
    now_playing_message: Optional[discord.Message] = None
    next: asyncio.Event = asyncio.Event()
    playlist: Playlist = field(default_factory=Playlist)

    def get_embed(self, title: str = None, playlist_page: int = 0) -> discord.Embed:
        np_link = (
            f'[{self.current_track.source.info.title}]'
            f'({self.current_track.source.info.webpage_url or self.current_track.url})'
        )
        embed = discord.Embed(
            title=title or 'Now playing',
            description=np_link,
        )
        embed.add_field(
            name='Duration',
            value=str(datetime.timedelta(seconds=self.current_track.source.info.duration)),
        )
        embed.add_field(
            name='Requested by',
            value=self.current_track.requested_by.mention,
        )
        embed.set_thumbnail(url=self.current_track.source.info.thumbnail)

        if self.playlist.queue:
            start_pos = playlist_page * config.EMBED_QUEUE_PER_PAGE
            end_pos = start_pos + config.EMBED_QUEUE_PER_PAGE
            display_queue = list(itertools.islice(self.playlist.queue, start_pos, end_pos))
            display_queue_fmt = '\n'.join(
                f'{i}.  [{track.source.info.title}]({track.source.info.webpage_url or track.url})'
                f'\nfrom {track.requested_by.mention}'
                for i, track in enumerate(display_queue, start=start_pos + 1)
            )
            embed.add_field(
                name='Up next:',
                value=display_queue_fmt,
                inline=False,
            )

        # Offsetting by 1, 'cause now playing song is in history
        history_offset = 1
        if len(self.playlist.history) > history_offset:
            display_history = list(
                itertools.islice(self.playlist.history, history_offset, config.EMBED_HISTORY_PER_PAGE + history_offset)
            )
            display_history_fmt = '\n'.join(
                f'{i}.  [{track.source.info.title}]({track.source.info.webpage_url or track.url})'
                f'\nfrom {track.requested_by.mention}'
                for i, track in enumerate(display_history, start=1)
            )
            embed.add_field(
                name='Recently played:',
                value=display_history_fmt,
                inline=False,
            )
        return embed

    def handle_source(self, request: str, requested_by: discord.Member) -> None:
        parsed_request = urlparse(request)
        if not parsed_request.scheme or parsed_request.netloc in youtube.Source.TAGS:
            # Search on YouTube or get from url
            youtube.Source.handle(request, self.playlist, requested_by)

    async def prev(self) -> None:
        prev_track = self.playlist.prev(self.current_track)
        vc: Optional[discord.VoiceClient] = self.guild.voice_client

        if not vc.is_playing():
            await self.play(prev_track)
        else:
            vc.stop()

    def next_track(self, error):
        next_track = self.playlist.next()
        self.current_track = None

        self.next.set()
        if next_track is None:
            return

        coroutine = self.play(next_track)
        self.bot.loop.create_task(coroutine)

    async def preload(self, track: Track):
        if track.loaded:
            return

        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        return await asyncio.wait(
            fs={loop.run_in_executor(executor, track.load)},
            return_when=asyncio.ALL_COMPLETED,
        )

    async def play(self, track: Track):
        self.next.clear()

        self.current_track = track
        if not self.current_track.loaded:
            self.current_track.load()

        self.playlist.history.appendleft(self.current_track)

        vc: Optional[discord.VoiceClient] = self.guild.voice_client
        vc.play(
            discord.FFmpegPCMAudio(
                self.current_track.url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            ),
            after=lambda err: self.next_track(err),
        )

        self.playlist.queue.popleft()
        self.now_playing_message = await self.channel.send(embed=self.get_embed())

        for track in list(self.playlist.queue)[1 : config.MAX_PRELOAD + 1]:
            asyncio.ensure_future(self.preload(track))

        await self.next.wait()
        try:
            # Remove "Now Playing" message of the song that ended
            await self.now_playing_message.delete()
        except discord.HTTPException:
            pass

    async def shuffle(self) -> None:
        self.playlist.shuffle()
        for track in list(self.playlist.queue)[1 : config.MAX_PRELOAD + 1]:
            asyncio.ensure_future(self.preload(track))
