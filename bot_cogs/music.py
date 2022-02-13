import asyncio

import discord
from discord.ext import commands

from core import utils
from general import guild_to_audioplayer


class Music(commands.Cog):
    """Music related commands"""

    __slots__ = ('bot',)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='connect', aliases=['join'])
    async def _join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
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
                await ctx.send('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                await ctx.send(f'Moving to channel: <#{channel.id}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                await ctx.send(f'Connecting to channel: <#{channel.id}> timed out.')

        await ctx.send(f'Connected to <#{channel.id}>', delete_after=20)

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Request a song and add it to the queue.

        This command attempts to join a valid Voice Channel if the bot is not already in one.

        Parameters
        -----------
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        await ctx.trigger_typing()

        if not ctx.voice_client:
            await ctx.invoke(self._join)

        player = guild_to_audioplayer[ctx.guild]
        player.channel = ctx.channel

        player.timer.cancel()
        player.timer = utils.Timer(player.timeout_handler)

        if player.playlist.loop:
            await ctx.send("Loop is enabled!  :repeat:")

        await player.process_track(ctx, search)

    @commands.command(name='loop', aliases=['l'])
    async def _loop(self, ctx: commands.Context):
        """Repeat the currently playing song."""
        player = guild_to_audioplayer[ctx.guild]
        player.playlist.loop = not player.playlist.loop
        await ctx.send(f'**`{ctx.author}`**: Loop {"enabled  :repeat:" if player.playlist.loop else "disabled  :x:"}')

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx):
        """Shuffle the playlist."""
        player = guild_to_audioplayer[ctx.guild]
        player.playlist.shuffle()
        await ctx.send(f'**`{ctx.author}`**: Shuffled the queue.')

    @commands.command(name='pause')
    async def _pause(self, ctx: commands.Context):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send("I'm not currently playing anything.", delete_after=20)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused the song.')

    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)
        elif vc.is_playing():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed the song.')

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        """Stop the currently playing song and destroy the player.

        !Warning!
        This will destroy the player assigned to your server, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently playing anything.", delete_after=20)
        player = guild_to_audioplayer[ctx.guild]
        await player.stop_player()
        await ctx.send(f'**`{ctx.author}`**: Stopped the player.')

    @commands.command(name='skip', aliases=['next'])
    async def _skip(self, ctx: commands.Context):
        """Skip the song.

        ToDo: vote skip?
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        player = guild_to_audioplayer[ctx.guild]
        player.playlist.loop = False

        player.timer.cancel()
        player.timer = utils.Timer(player.timeout_handler)

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: Skipped the song.')

    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def _queue_info(self, ctx: commands.Context, page_num: int = None):
        """Retrieve a basic queue of upcoming songs.

        Parameters
        -----------
        page_num: int [Optional]
            Playlist page number to display.
        """
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        player = guild_to_audioplayer[ctx.guild]

        embed = player.playlist.create_embed(title='Playlist', page_num=page_num)

        if embed is None:
            return await ctx.send('There are currently no more queued songs.')
        await ctx.send(embed=embed)

    @commands.command(name='clear')
    async def _clear(self, ctx: commands.Context):
        """Clear the current playlist."""
        player = guild_to_audioplayer[ctx.guild]
        player.playlist.clear()

        await ctx.send(f'**`{ctx.author}`**: Cleared the queue.')
        # # ToDo: Do I need to stop now playing track?
        # ctx.guild.voice_client.stop()
        # player.playlist.loop = False

    @commands.command(name='prev')
    async def _prev(self, ctx: commands.Context):
        """Play the last song."""
        vc = ctx.voice_client
        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        player = guild_to_audioplayer[ctx.guild]
        player.playlist.loop = False

        player.timer.cancel()
        player.timer = utils.Timer(player.timeout_handler)

        await player.prev_track()
        await ctx.send('Playing previous song.')

    @commands.command(name='np', aliases=['current'])
    async def _now_playing(self, ctx: commands.Context):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        player = guild_to_audioplayer[ctx.guild]
        if not player.current_track:
            return await ctx.send("I'm not currently playing anything.", delete_after=20)

        try:
            # Remove "Now Playing" message of the song that ended
            await player.np_message.delete()
        except discord.HTTPException:
            pass

        player.np_message = await ctx.send(embed=player.current_track.create_embed())

    @commands.command(name='history', aliases=['h'])
    async def _history(self, ctx: commands.Context):
        """Retrieve a basic list of recently played songs."""
        player = guild_to_audioplayer[ctx.guild]

        embed = player.playlist.create_embed(title='Recently played')

        if embed is None:
            return await ctx.send('History is empty.')
        await ctx.send(embed=embed)

    @commands.command(name='delete', aliases=['remove', 'del'])
    async def _delete(self, ctx: commands.Context, *, position: int):
        """Remove song by index from the queue.

        Parameters
        -----------
        position: int [Required]
            History page number to display.
        """
        player = guild_to_audioplayer[ctx.guild]
        playlist = player.playlist
        try:
            if len(playlist) == 0:
                return

            position = position - 1

            if not 0 <= position < len(playlist):
                await ctx.send(f'Please specify the correct index of a song to remove.', delete_after=15)
                return

            removed_track = playlist.delete(position)
            await ctx.send(f'**`{ctx.author}`**: Removed `{removed_track.info.title}`.')
        finally:
            await ctx.invoke(self._queue_info)

    @_delete.error
    async def _delete__error(self, ctx, error):
        if isinstance(error, commands.errors.BadArgument):
            await ctx.send(f'Please specify the correct index of a song to remove.', delete_after=15)

    @_queue_info.error
    async def _queue_info__error(self, ctx, error):
        if isinstance(error, commands.errors.BadArgument):
            await ctx.send('Nice try you rascal :knife:', delete_after=5)
            await ctx.invoke(self._queue_info)

    @_history.error
    async def _history__error(self, ctx, error):
        if isinstance(error, commands.errors.BadArgument):
            await ctx.send('Nice try you rascal :knife:', delete_after=5)
            await ctx.invoke(self._history)

    @_join.before_invoke
    @_play.before_invoke
    @_delete.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You are not connected to any voice channel.', delete_after=20)
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send(f'I am already in a voice channel. Join me at <#{ctx.voice_client.channel.id}>')
                return


def setup(bot):
    bot.add_cog(Music(bot))
