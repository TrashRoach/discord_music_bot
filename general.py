import logging
import os
from pathlib import Path

import discord
from discord.ext import commands

from config import BOT_CMD_PREFIX
from core.music_player import MusicPlayer
from core.settings import Settings

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
                bot.load_extension(f'{COG_FOLDER}.{cog}')
                logging.info(f'{cog} cog has been loaded!')
            except commands.errors.ExtensionAlreadyLoaded:
                logging.info(f'{cog} cog is already loaded!')
            except commands.errors.ExtensionFailed as ex:
                logging.warning(f'{cog} cog failed to load! \n{ex}')
        for guild in bot.guilds:
            guild_to_settings[guild] = Settings(guild)
            guild_to_audioplayer[guild] = MusicPlayer(bot, guild)
        logging.info(f'{bot.user.name} - Ready!')

    @bot.event
    async def on_connect():
        logging.info(f'{bot.user.name} - Connected!')

    @bot.event
    async def on_disconnect():
        logging.info(f'{bot.user.name} - Disconnected!')
