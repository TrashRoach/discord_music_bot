import asyncio
import concurrent.futures
from urllib.parse import urlparse

import discord
import yt_dlp
from discord.ext import commands

from core import utils
from core.playlist import Playlist
from core.track import Track


class MusicPlayer(object):
    __slots__ = ('bot', 'playlist', 'current_track', 'next', 'np_message', 'guild', 'channel', '_volume', 'timer')

    def __init__(self, bot, guild):
        self.bot = bot
        self.playlist = Playlist()
        self.current_track = None
        self.next = asyncio.Event()
        self.np_message = None
        self.guild = guild
        self.channel = None
        self._volume = 0.5
        self.timer = utils.Timer(self.timeout_handler)

    async def timeout_handler(self):
        # Terminate the player and DC if left alone :(
        if len(self.guild.voice_client.channel.voice_states) == 1:
            await self.stop_player()
            await self.guild.voice_client.disconnect(force=True)
            return

        # Reset DC timer if still playing
        if self.guild.voice_client.is_playing():
            self.timer = utils.Timer(self.timeout_handler)
            return

        await self.stop_player()
        await self.guild.voice_client.disconnect(force=True)

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        try:
            self.guild.voice_client.source.volume = float(value) / 100.0
        except Exception as e:
            pass

    async def play_track(self, track):

        if not self.playlist.loop:
            self.timer.cancel()
            self.timer = utils.Timer(self.timeout_handler)

        self.next.clear()
        if track.info.duration is None:
            ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'title': True})
            r = ytdl.extract_info(track.info.webpage_url, download=False)
            track.url = r.get('url')
            track.info.uploader = r.get('uploader')
            track.info.title = r.get('title')
            track.info.duration = r.get('duration')
            track.info.webpage_url = r.get('webpage_url')
            track.info.thumbnail = r.get('thumbnails')[0]['url']

        self.current_track = track

        self.playlist.play_history.append(self.current_track)

        self.guild.voice_client.play(discord.FFmpegPCMAudio(
            track.url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
            after=lambda err: self.next_track(err)
        )
        self.np_message = await self.channel.send(embed=track.create_embed())
        self.playlist.play_queue.popleft()
        await self.next.wait()
        try:
            # Remove "Now Playing" message of the song that ended
            await self.np_message.delete()
        except discord.HTTPException:
            pass
        for track in list(self.playlist.play_queue)[1:6]:
            asyncio.ensure_future(self.preload(track))

    def next_track(self, error):
        next_track = self.playlist.next()
        self.current_track = None

        self.next.set()
        if next_track is None:
            return

        coro = self.play_track(next_track)
        self.bot.loop.create_task(coro)

    async def prev_track(self):

        self.timer.cancel()
        self.timer = utils.Timer(self.timeout_handler)

        if len(self.playlist.play_history) == 0:
            return

        prev_track = self.playlist.prev(self.current_track)

        if not self.guild.voice_client.is_playing() and not self.guild.voice_client.is_paused():
            await self.play_track(prev_track)
        else:
            self.guild.voice_client.stop()

    async def process_playlist(self, ctx: commands.Context, search):
        composed_msg = f'Added '
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'extract_flat': True}) as ytdl:
            r = ytdl.extract_info(search, download=False)
            entries = r.get('entries')
            # ToDo: hardcoded max_playlist_len
            max_playlist_len = 25
            if len(entries) > max_playlist_len:
                await ctx.send(f'Too much songs in requested playlist. Maximum is {max_playlist_len}.')
                entries = entries[:25]
            for entry in entries:
                track_obj = Track(
                    requester=ctx.author,
                    title=entry.get('title'),
                    webpage_url=entry.get('url')
                )
                self.playlist.add(track_obj)
                composed_msg += f'\n`{track_obj.info.title}`'

        await ctx.send(f'{composed_msg} to the Queue.', delete_after=15)
        for track in list(self.playlist.play_queue)[1:6]:
            asyncio.ensure_future(self.preload(track))

    async def preload(self, track_obj):
        if track_obj.info.duration is not None:
            return

        def download(track):
            if track.info.webpage_url is None:
                print(f'{track.info.webpage_url = }')
                return None

            ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'title': True})
            r = ytdl.extract_info(track.info.webpage_url, download=False)
            track.url = r.get('url')
            track.info.uploader = r.get('uploader')
            track.info.title = r.get('title')
            track.info.duration = r.get('duration')
            track.info.webpage_url = r.get('webpage_url')
            track.info.thumbnail = r.get('thumbnails')[0]['url']

        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        await asyncio.wait(fs={loop.run_in_executor(executor, download, track_obj)}, return_when=asyncio.ALL_COMPLETED)

    def search_youtube(self, search: str):
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'default_search': 'auto', 'noplaylist': True}) as ytdl:
            r = ytdl.extract_info(search, download=False)

        if r is None:
            return None

        return r['entries'][0]

    async def process_track(self, ctx: commands.Context, search: str):

        result = urlparse(search)

        if result.path == '/playlist':
            await self.process_playlist(ctx, search)
            if self.current_track is None:
                await self.play_track(self.playlist.play_queue[0])
                return
        if not result.scheme:
            r = self.search_youtube(search)
            if r is None:
                await ctx.channel.send('Could not find anything on YouTube. Sorry.')
                return
        else:
            try:
                ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'title': True})

                try:
                    r = ytdl.extract_info(search, download=False)
                except Exception as ex:
                    await self.channel.send(f'There was an error processing your request.\n'
                                            f'```css\n{ex}\n```')
                    return None
            except Exception as ex:
                ytdl = yt_dlp.YoutubeDL({'title': True})
                r = ytdl.extract_info(search, download=False)

        if r.get('thumbnails') is not None:
            thumbnail = r.get('thumbnails')[len(r.get('thumbnails')) - 1]['url']
        else:
            thumbnail = None

        track_obj = Track(
            url=r.get('url'),
            requester=ctx.author,
            uploader=r.get('uploader'),
            title=r.get('title'),
            duration=r.get('duration'),
            webpage_url=r.get('webpage_url'),
            thumbnail=thumbnail
        )

        self.playlist.add(track_obj)
        composed_msg = f'Added '
        composed_msg += f'`{track_obj.info.title}`'
        await ctx.send(f'{composed_msg} to the Queue.', delete_after=15)

        if self.current_track is None:
            await self.play_track(self.playlist.play_queue[0])

        return

    async def stop_player(self):
        self.playlist.loop = False
        self.playlist.next()
        self.playlist.clear()
        self.guild.voice_client.stop()
