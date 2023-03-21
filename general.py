import logging
import os
from pathlib import Path

import discord
from discord.ext import commands

from config import BOT_CMD_PREFIX
from core.settings import settings_setup

BASE_DIR = Path(__file__).resolve().parent
COG_FOLDER = "bot_cogs"
COG_LIST = [cog[:-3] for cog in os.listdir(BASE_DIR.joinpath(COG_FOLDER)) if not cog.startswith('_')]

guild_to_audioplayer = {}
guild_to_settings = {}

logging.basicConfig(
    format='%(asctime)-s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%d.%m.%Y %H:%M:%S')


def setup(bot):
    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(name=f'{BOT_CMD_PREFIX}play'))
        for cog in COG_LIST:
            try:
                await bot.load_extension(f'{COG_FOLDER}.{cog}')
                logging.info(f'[ + ] {cog}')
            except commands.errors.ExtensionAlreadyLoaded:
                logging.info(f'[   ] {cog}')
            except commands.errors.ExtensionFailed as ex:
                logging.warning(f'[ X ] {cog}\n{ex}')
        for guild in bot.guilds:
            settings_setup(
                bot=bot,
                guild=guild,
                guild_to_settings=guild_to_settings,
                guild_to_audioplayer=guild_to_audioplayer
            )
        logging.info(f'{bot.user.name} - Ready!')

    @bot.event
    async def on_guild_join(guild):
        """
        Called when a Guild is either created by the Client or when the Client joins a guild.

        :param guild: (Guild) – The guild that was joined.
        """
        settings_setup(
            bot=bot,
            guild=guild,
            guild_to_settings=guild_to_settings,
            guild_to_audioplayer=guild_to_audioplayer
        )

    @bot.event
    async def on_connect():
        logging.info(f'{bot.user.name} - Connected!')

    @bot.event
    async def on_disconnect():
        logging.info(f'{bot.user.name} - Disconnected!')
