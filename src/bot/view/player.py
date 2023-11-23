from enum import Enum
from typing import TYPE_CHECKING, Optional

import discord
from discord import VoiceClient

if TYPE_CHECKING:
    from src.music.player import Player


class PlayerEmoji(Enum):
    PREV = '\U000023EE'
    PAUSE = '\U000023F8'
    PLAY = '\U000025B6'
    NEXT = '\U000023ED'
    SHUFFLE = '\U0001F500'
    STOP = '\U000023F9'
    LOOP = '\U0001F501'


class MusicPlayerView(discord.ui.View):
    def __init__(self, player: 'Player'):
        super().__init__(timeout=None)
        self.player = player
        self.prev.disabled = len(self.player.playlist.history) <= 1
        self.next.disabled = not len(self.player.playlist.queue)
        self.shuffle.disabled = len(self.player.playlist.queue) <= 1
        self.set_loop_style()

    def set_loop_style(self):
        self.loop.style = discord.ButtonStyle.green if self.player.playlist.loop else discord.ButtonStyle.blurple

    @discord.ui.button(emoji=PlayerEmoji.PREV.value, style=discord.ButtonStyle.blurple, label=None)
    async def prev(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        self.play_pause.emoji = PlayerEmoji.PAUSE.value
        self.play_pause.style = discord.ButtonStyle.blurple

        response: discord.InteractionResponse = interaction.response
        await response.defer(ephemeral=True)

        await self.player.prev()

    @discord.ui.button(emoji=PlayerEmoji.PAUSE.value, style=discord.ButtonStyle.blurple, label=None)
    async def play_pause(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        embed_title = ''
        vc: Optional[VoiceClient] = interaction.guild.voice_client
        if not vc:
            return

        if vc.is_playing():
            self.play_pause.emoji = PlayerEmoji.PLAY.value
            vc.pause()
            embed_title = 'Paused'
        else:
            self.play_pause.emoji = PlayerEmoji.PAUSE.value
            vc.resume()

        response: discord.InteractionResponse = interaction.response
        await response.edit_message(embed=self.player.get_embed(title=embed_title), view=self)

    @discord.ui.button(emoji=PlayerEmoji.NEXT.value, style=discord.ButtonStyle.blurple, label=None)
    async def next(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        self.play_pause.emoji = PlayerEmoji.PAUSE.value
        self.play_pause.style = discord.ButtonStyle.blurple

        response: discord.InteractionResponse = interaction.response
        await response.defer(ephemeral=True)

        vc: Optional[VoiceClient] = interaction.guild.voice_client
        if not vc:
            return
        vc.stop()

    @discord.ui.button(label='Prev page', style=discord.ButtonStyle.secondary, disabled=True)
    async def playlist_prev(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""

    @discord.ui.button(emoji=PlayerEmoji.SHUFFLE.value, row=2, style=discord.ButtonStyle.blurple, label=None)
    async def shuffle(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        await self.player.shuffle()
        author: discord.Member = interaction.user

        response: discord.InteractionResponse = interaction.response
        await response.edit_message(
            content=f'{author.mention} shuffled the queue.', embed=self.player.get_embed(), view=self
        )  # noqa  # TODO

    @discord.ui.button(
        row=2, emoji=PlayerEmoji.STOP.value, style=discord.ButtonStyle.blurple, label=None, disabled=True
    )
    async def stop(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        await interaction.response.edit_message(content='stop', embed=self.embed, view=self)  # noqa  # TODO

    @discord.ui.button(row=2, emoji=PlayerEmoji.LOOP.value, style=discord.ButtonStyle.blurple, label=None)
    async def loop(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        self.player.playlist.loop = not self.player.playlist.loop
        self.set_loop_style()

        response: discord.InteractionResponse = interaction.response
        await response.edit_message(embed=self.player.get_embed(), view=self)

    @discord.ui.button(row=2, label='Next page', style=discord.ButtonStyle.secondary)
    async def playlist_next(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """TODO"""
        pass
