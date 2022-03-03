import asyncio
import concurrent.futures
from urllib.parse import urlparse, parse_qs

import discord
import yt_dlp
from discord.ext import commands

from config import MAX_SONG_DURATION, MAX_PRELOAD, MAX_PLAYLIST_LEN
from core import utils
from core.playlist import Playlist
from core.track import Track


class MusicPlayer(object):
    __slots__ = ('bot', 'playlist', 'current_track', 'next', 'np_message', 'guild', 'channel', 'timer')

    def __init__(self, bot, guild):
        self.bot = bot
        self.playlist = Playlist()
        self.current_track = None
        self.next = asyncio.Event()
        self.np_message = None
        self.guild = guild
        self.channel = None
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

    async def play_track(self, track):

        if not self.playlist.loop:
            self.timer.cancel()
            self.timer = utils.Timer(self.timeout_handler)

        self.next.clear()
        if track.info.duration is None:
            ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'title': True})
            info = ytdl.extract_info(track.info.webpage_url, download=False)
            track.url = info.get('url')
            track.info.uploader = info.get('uploader')
            track.info.title = info.get('title')
            track.info.duration = info.get('duration')
            track.info.webpage_url = info.get('webpage_url')
            track.info.thumbnail = info.get('thumbnails')[0]['url']

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
        for track in list(self.playlist.play_queue)[1:MAX_PRELOAD + 1]:
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

    async def process_playlist(self, ctx: commands.Context, search, start_pos: int = 0):
        composed_msg = f'**Added**\n'
        excluded = []
        with yt_dlp.YoutubeDL(
                {
                    'format': 'bestaudio/best',
                    'extract_flat': True,
                    'playliststart': start_pos,
                    'playlistend': start_pos + MAX_PLAYLIST_LEN + 1
                }
        ) as ytdl:
            info = ytdl.extract_info(search, download=False)
        entries = info.get('entries')
        for entry in entries:
            track_duration = entry.get('duration')
            if track_duration is None or track_duration > MAX_SONG_DURATION:
                excluded.append(entry.get('title') if track_duration else entry.get('url'))
                continue
            track_obj = Track(
                requester=ctx.author,
                title=entry.get('title'),
                webpage_url=entry.get('url')
            )
            self.playlist.add(track_obj)
            composed_msg += f'\n`{track_obj.info.title}`'

        composed_msg = f'{composed_msg} to the Queue.\n\n'
        if excluded:
            composed_msg += '\n**Excluded (song is private or too long)**\n'
            composed_msg += '\n'.join(f'`{track}`' for track in excluded)

        if len(composed_msg) > 2000:
            part_1 = composed_msg[:2000]
            slice_index = part_1.rfind('\n')
            part_1 = part_1[:slice_index]
            composed_msg = '...' + composed_msg[slice_index:]
            await ctx.send(part_1, delete_after=25)

        await ctx.send(composed_msg, delete_after=25)
        for track in list(self.playlist.play_queue)[1:MAX_PRELOAD + 1]:
            asyncio.ensure_future(self.preload(track))

    async def preload(self, track_obj):
        if track_obj.info.duration is not None:
            return

        def download(track):
            if track.info.webpage_url is None:
                print(f'{track.info.webpage_url = }')
                return None

            ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'title': True})
            info = ytdl.extract_info(track.info.webpage_url, download=False)
            track.url = info.get('url')
            track.info.uploader = info.get('uploader')
            track.info.title = info.get('title')
            track.info.duration = info.get('duration')
            track.info.webpage_url = info.get('webpage_url')
            track.info.thumbnail = info.get('thumbnails')[0]['url']

        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        await asyncio.wait(fs={loop.run_in_executor(executor, download, track_obj)}, return_when=asyncio.ALL_COMPLETED)

    def search_youtube(self, search: str):
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'default_search': 'auto', 'noplaylist': True}) as ytdl:
            info = ytdl.extract_info(search, download=False)

        if info is None:
            return None

        return info['entries'][0]

    async def process_track(self, ctx: commands.Context, search: str):
        await ctx.trigger_typing()
        result = urlparse(search)
        if 'start_radio' in result.query:
            await ctx.channel.send('You can\'t request YouTube Mixes. Sorry.', delete_after=15)
            return
        if result.path == '/playlist' or 'list=' in result.query:
            link_params = parse_qs(search)
            start_pos = link_params.get('index', 0)
            if start_pos:
                start_pos = int(start_pos[0])

            # Default link params start with 'watch',
            # which makes yt-dlp think that its not a playlist for some reason
            id_list = link_params.get('list') \
                      or [val for key, val in link_params.items() if 'list' in key][0]  # Scuffed fix for youtu.be
            search = f'https://www.youtube.com/playlist?list={id_list[0]}'

            await self.process_playlist(ctx, search, start_pos)
            if self.current_track is None:
                await self.play_track(self.playlist.play_queue[0])
                return
        if not result.scheme:
            info = self.search_youtube(search)
            if info is None:
                await ctx.channel.send('Could not find anything on YouTube. Sorry.')
                return
        else:
            try:
                ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'title': True})

                try:
                    info = ytdl.extract_info(search, download=False)
                except Exception as ex:
                    await self.channel.send(f'There was an error processing your request.\n'
                                            f'```css\n{ex}\n```')
                    return None
            except Exception as ex:
                ytdl = yt_dlp.YoutubeDL({'title': True})
                info = ytdl.extract_info(search, download=False)

        if info.get('thumbnails') is not None:
            thumbnail = info.get('thumbnails')[len(info.get('thumbnails')) - 1]['url']
        else:
            thumbnail = None
        if info.get('duration') > MAX_SONG_DURATION:
            await ctx.send(f'Sorry, `{info.get("title")}` is too long.')
            return
        track_obj = Track(
            url=info.get('url'),
            requester=ctx.author,
            uploader=info.get('uploader'),
            title=info.get('title'),
            duration=info.get('duration'),
            webpage_url=info.get('webpage_url'),
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
