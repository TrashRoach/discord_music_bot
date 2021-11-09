import logging
import os
from pathlib import Path

import discord
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent
COG_FOLDER = "bot_cogs"
COG_LIST = [cog[:-3] for cog in os.listdir(BASE_DIR.joinpath(COG_FOLDER)) if not cog.startswith('_')]

logging.basicConfig(
    format='%(asctime)-s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%d.%m.%Y %H:%M:%S')


def setup(bot):
    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(name=f'{bot.command_prefix}play'))
        for cog in COG_LIST:
            try:
                bot.load_extension(f'{COG_FOLDER}.{cog}')
                logging.info(f'{cog} cog has been loaded!')
            except commands.errors.ExtensionAlreadyLoaded:
                logging.info(f'{cog} cog is already loaded!')
            except commands.errors.ExtensionFailed:
                logging.warning(f'{cog} cog failed to load!')

        logging.info(f'{bot.user.name} - Ready!')

    @bot.event
    async def on_connect():
        logging.info(f'{bot.user.name} - Connected!')

    @bot.event
    async def on_disconnect():
        logging.debug(f'{bot.user.name} - Disconnected!')