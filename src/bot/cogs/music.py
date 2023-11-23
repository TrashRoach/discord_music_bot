import asyncio
from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from src.bot.cogs._base import BaseCog
from src.config import GUILD_TO_MUSIC_PLAYER

if TYPE_CHECKING:
    from src.music.player import Player


class Music(BaseCog):
    """Music related commands"""

    @commands.hybrid_command(name='join')
    async def _join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send('No channel to join. Please either specify a valid channel or join one.')

        if vc := ctx.voice_client:
            if vc.channel.id == channel.id:  # noqa
                return
            try:
                await vc.move_to(channel)  # noqa
            except asyncio.TimeoutError:
                await ctx.send(f'Moving to channel: <#{channel.id}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                await ctx.send(f'Connecting to channel: <#{channel.id}> timed out.')

        await ctx.send(f'Connected to <#{channel.id}>', delete_after=10)

    @commands.hybrid_command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        await ctx.message.delete()

        vc: Optional[discord.VoiceClient] = ctx.voice_client
        if not vc:
            await ctx.invoke(self._join)

        player: Player = GUILD_TO_MUSIC_PLAYER[ctx.guild.id]
        player.channel = ctx.channel

        player.handle_source(request=search, requested_by=ctx.message.author)

        if player.current_track is None:
            await player.play(player.playlist.next())
            return

        await player.now_playing_message.edit(embed=player.get_embed(), view=player.view)

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You are not connected to any voice channel.', delete_after=20)
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send(f'I am already in a voice channel. Join me at <#{ctx.voice_client.channel.id}>')
                return

    @commands.cooldown(1, 5)
    @commands.hybrid_command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """Skip the song.

        ToDo: vote skip?
        """
        vc: Optional[discord.VoiceClient] = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("I'm not currently connected to voice.", delete_after=20)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: Skipped the song.')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
