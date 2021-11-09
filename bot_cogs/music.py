import logging

import discord
from discord.ext import commands

import asyncio
import itertools
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors"""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels"""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """
        Allows to access attributes similar to a dict
        Useful only when NOT downloading
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, data, download=False):
        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {
                'webpage_url': data['webpage_url'],
                'requester': ctx.author,
                'title': data['title']
            }
        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """
        For preparing a stream, instead of downloading
        Since Youtube Streaming links expire
        """
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)
        if 'entries' in data:
            # ToDo: take first item from a playlist
            data = data['entries'][0]
        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    """
    A class assigned to each guild using one Music Bot

    Implements a queue and loop, which allows for different guilds to listen to different playlists simultaneously

    When the bot dc from the VoiceChannel it's instance will be destroyed
    """

    __slots__ = (
        'bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume'
    )

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Main player loop"""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song
                # In case of timeout cancel the player and disconnect
                async with timeout(300):  # 5min
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                if self in self._cog.players.values():
                    return self.destroy(self._guild)
                return

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as ex:
                    await self._channel.send(f'There was an error processing your request.\n'
                                             f'```css\n{ex}\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**Now Playing:** ▶️ `{source.title}` '
                                               f'requested by `{source.requester}`')
            await self.next.wait()

            # Cleanup FFmpeg process
            source.cleanup()
            self.current = None

            try:
                # Remove the song that ended
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, _guild):
        """Disconnect and cleanup the player"""
        return self.bot.loop.create_task(self._cog.cleanup(_guild))


class Music(commands.Cog):
    """Music related commands"""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            for entry in self.players[guild.id].queue._queue:
                if isinstance(entry, YTDLSource):
                    entry.cleanup()
            self.players[guild.id].queue._queue.clear()
        except KeyError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('Do not use me in Private Messages')
            except discord.HTTPException:
                pass

        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in valid channel or provide me with one.')

        logging.warning(f'Ignoring exception in command {ctx.command}:\n'
                        f'{error}\n'
                        f'{error.__traceback__}')

    def get_player(self, ctx):
        """Retrieve or generate the guild player."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connect', aliases=['join'])
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to Voice Channel.

        Parameters
        -----------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to.
            If a channel is not specified, an attempt to join the voice channel you are in will be made.

        This command also handles moving a bot to different channels.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <#{channel.id}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <#{channel.id}> timed out.')

        await ctx.send(f'Connected to <#{channel.id}>', delete_after=20)

    @commands.command(name='play', aliases=['p'])
    async def play_(self, ctx, *, search: str):
        """Request a song and add it it the queue.

        This command attempts to join a valid Voice Channel if the bot is not already in one.
        Uses YTDL to automatically search and retrieve a song.

        Parameters
        -----------
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        await ctx.trigger_typing()
        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        to_run = partial(ytdl.extract_info, url=search, download=False)

        loop = self.bot.loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, to_run)
        composed_msg = f'Added '
        data_playlist = []
        if 'entries' in data:
            data_playlist = data['entries']
        if data_playlist:
            max_playlist_length = 25
            if len(data_playlist) > max_playlist_length:
                return await ctx.send(f"Requested playlist is too long.\n"
                                      f"Maximum length is set to **{max_playlist_length}**", delete_after=20)
            composed_msg += '\n'
            for data in data_playlist:
                source = await YTDLSource.create_source(ctx, data, download=False)
                await player.queue.put(source)
                composed_msg += f'`{data["title"]}`\n'
        else:
            source = await YTDLSource.create_source(ctx, data, download=False)
            await player.queue.put(source)
            composed_msg += f'`{data["title"]}`'
        await ctx.send(f'{composed_msg} to the Queue.', delete_after=15)

    @commands.command(name='pause')
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send("I'm not currently playing anything.", delete_after=20)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused the song.')

    @commands.command(name='resume')
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)
        elif vc.is_playing():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed the song.')

    @commands.command(name='skip')
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: Skipped the song.')

    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('There are currently no more queued songs.')

        # Grab up to 10 entries from the queue
        upcoming = list(itertools.islice(player.queue._queue, 0, 10))
        fmt = '\n'.join(f'**`{i}.  {song["title"]}`** requested by {song["requester"]}'
                        for i, song in enumerate(upcoming, start=1))
        embed = discord.Embed(
            title=f'Playlist - Next {len(upcoming)}',
            description=fmt
        )

        await ctx.send(embed=embed)

    @commands.command(name='np', aliases=['now_playing', 'current', 'currentsong', 'playing'])
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send("I'm not currently playing anything.", delete_after=20)

        try:
            # Remove previous Now Playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass

        player.np = await ctx.send(f'**Now Playing:** ▶️ `{vc.source.title}` '
                                   f'requested by `{vc.source.requester}`')

    @commands.command(name='volume', aliases=['vol'], hidden=True)
    async def change_volume(self, ctx, *, volume: float):
        """Change the player volume.

        Parameters
        -----------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        if not 0 < volume <= 100:
            return await ctx.send('Please enter a value between 1 and 100.')

        player = self.get_player(ctx)

        if vc.source:
            vc.volume = volume / 100

        player.volume = volume / 100
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{volume}%**')

    @commands.command(name='stop')
    async def stop_(self, ctx):
        """Stop the currently playing song and destroy the player.

        !Warning!
            This will destroy the player assigned to your server, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently playing anything.", delete_after=20)

        await self.cleanup(ctx.guild)


def setup(bot):
    bot.add_cog(Music(bot))
