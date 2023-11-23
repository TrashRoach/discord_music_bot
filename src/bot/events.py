import logging

import discord
from discord.ext import commands

from src.config import GUILD_TO_MUSIC_PLAYER
from src.music.player import Player

logger = logging.getLogger(__name__)


def setup_events(bot: commands.Bot):
    """
    God is dead.
    God remains dead.
    And we have killed him.
    """

    @bot.event
    async def on_ready():
        activity = discord.Activity(type=discord.ActivityType.playing, name='Music')
        await bot.change_presence(activity=activity)
        for guild in bot.guilds:
            GUILD_TO_MUSIC_PLAYER[guild.id] = Player(bot=bot, guild=guild)
        logger.info(f'{bot.user.name} - Ready!')

    @bot.event
    async def on_connect():
        logger.info(f'{bot.user.name} - Connected!')

    @bot.event
    async def on_disconnect():
        logger.debug(f'{bot.user.name} - Disconnected!')
